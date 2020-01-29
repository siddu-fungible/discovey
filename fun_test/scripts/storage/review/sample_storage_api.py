from lib.system.fun_test import *
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.review.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes


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


class RunStorageApiCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create Volume and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol"
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize()

        fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

        vol_uuid_dict = self.storage_controller_template.create_volume(fs_obj_list=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)

        hosts = self.topology.get_hosts()
        for fs_obj in vol_uuid_dict:
            for host_id in hosts:
                host_obj = hosts[host_id]
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=fs_obj,
                                                                                   volume_uuid=vol_uuid_dict[fs_obj],
                                                                                   validate_nvme_connect=True,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume")

    def run(self):
        hosts = self.topology.get_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
                                                                                filename="/dev/"+nvme_device_name)
            fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            fun_test.log(traffic_result)

    def cleanup(self):
        # self.storage_controller_template.cleanup()
        pass


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RunStorageApiCommands())
    setup_bringup.run()
