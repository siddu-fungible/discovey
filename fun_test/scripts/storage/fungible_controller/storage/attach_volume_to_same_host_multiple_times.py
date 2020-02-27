from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import *
from lib.system import utils
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


class VolumeManagement(FunTestCase):
    topology = None
    storage_controller_template = None
    fs_obj = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create given type of volume",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create volumes using API Call
                              ''')

    def setup(self, enable_encryption=False, skip_initialize=False, stripe_enabled=False, ec_vol=False):
        self.topology = fun_test.shared_variables["topology"]
        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            self.fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(self.fs_obj)

        if ec_vol:
            capacity = 107374182400
        else:
            min_volume_capacity = 1073741824
            max_volume_capacity = find_min_drive_capacity(self.fs_obj.get_storage_controller(),command_timeout=30)
            max_volume_capacity = max_volume_capacity - (3*4096)
            capacity = random.randint(min_volume_capacity,max_volume_capacity)
            capacity = capacity - (capacity%4096)

        compression_effort = 0
        if enable_encryption:
            encrypt = True
        else:
            encrypt = False
        if stripe_enabled:
            stripe_count = 12
        else:
            stripe_count = 0
        self.volume_count = 1
        self.run_traffic = False
        if ec_vol:
            self.storage_controller_template = EcVolumeOperationsTemplate(topology=self.topology)
            vol_type = VolumeTypes().EC
            vol_name = "ec_vol"
        else:
            self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
            vol_type = VolumeTypes().LOCAL_THIN
            vol_name = "blt_vol"

        if not skip_initialize:
            self.storage_controller_template.initialize()

        vol_uuid_dict = {}
        self.final_vol_uuid_dict = {}
        for x in range(1, self.volume_count + 1, 1):
            #name = vol_name + str(x)
            suffix = utils.generate_uuid(length=4)
            name = vol_name + suffix
            body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={"num_redundant_dpus": 0,
                                                                                                 "num_failed_disks": 2},
                                                               stripe_count=stripe_count)
            vol_uuid_dict = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                           body_volume_intent_create=body_volume_intent_create)
            self.final_vol_uuid_dict[x] = vol_uuid_dict
            fun_test.test_assert(expression=vol_uuid_dict, message="Create volume{} with uuid {}"
                                 .format(x, vol_uuid_dict[0]))

        self.hosts = self.topology.get_available_hosts()
        for host_id in self.hosts:
            host_obj = self.hosts[host_id]
            for x in range(1, self.volume_count + 1, 1):
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=self.fs_obj,
                                                                                   volume_uuid=self.final_vol_uuid_dict[
                                                                                       x][0],
                                                                                   validate_nvme_connect=False,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume with uuid {} Successful"
                                     .format(self.final_vol_uuid_dict[x][0]))
        self.attach_multiple()

    def attach_multiple(self):
        count = 100
        for i in range(count):
            for host_id in self.hosts:
                host_obj = self.hosts[host_id]
                for x in range(1, self.volume_count + 1, 1):
                    attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=self.fs_obj,
                                                                                       volume_uuid=self.final_vol_uuid_dict[
                                                                                           x][0],
                                                                                       validate_nvme_connect=False,
                                                                                       raw_api_call=True)

                    fun_test.test_assert_expected(expected="Attach failed when creating port",
                                                  actual=attach_vol_result[0]['error_message'], message="Volume is already attached" )

    def run(self):
        hosts = self.topology.get_available_hosts()
        if self.run_traffic:
            for host_id in hosts:
                host_obj = hosts[host_id]
                nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
                traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
                                                                                    filename="/dev/" + nvme_device_name)
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

class RawVolMultipleAttach(VolumeManagement):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Attach RAW volume to same host multiple times ",
                              test_rail_case_ids=["C34957"],
                              steps='''1. Make sure API server is up and running
                              2. Create a RAW volume using API Call
                              3. Attach volume to the same host 100 times
                              ''')

    def setup(self):
        super(RawVolMultipleAttach, self).setup(enable_encryption=False, skip_initialize=True, stripe_enabled=False)

    def run(self):
        super(RawVolMultipleAttach, self).run()

    def cleanup(self):
        super(RawVolMultipleAttach, self).cleanup()


class ECVolMultipleAttach(VolumeManagement):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Attach EC(4+2) volume to same host multiple times",
                              test_rail_case_ids=["C34958"],
                              steps='''1. Make sure API server is up and running
                              2. Create an EC volume using API Call
                              3. Attach volume to the same host 100 times
                              ''')

    def setup(self):
        super(ECVolMultipleAttach, self).setup(enable_encryption=False, skip_initialize=True, stripe_enabled=False,
                                               ec_vol=True)

    def run(self):
        super(ECVolMultipleAttach, self).run()

    def cleanup(self):
        super(ECVolMultipleAttach, self).cleanup()



if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RawVolMultipleAttach())
    #setup_bringup.add_test_case(ECVolMultipleAttach())
    setup_bringup.run()
