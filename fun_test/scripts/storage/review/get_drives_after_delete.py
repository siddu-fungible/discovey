from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
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

    def cleanup(self):
        self.topology.cleanup()


class RunStorageApiCommands(FunTestCase):
    topology = None
    storage_controller_template = None
    drives = []

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
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        fs_obj_list = [self.topology.get_dut_instance(index=dut_index)
                       for dut_index in self.topology.get_available_duts().keys()]
        storage_controller = fs_obj_list[0].get_storage_controller()
        self.storage_controller_template.get_health(fs_obj=fs_obj_list[0])
        topology_result = storage_controller.topology_api.get_hierarchical_topology()
        fun_test.log(topology_result)
        for node in topology_result.data:
            for dpu in topology_result.data[node].dpus:
                for drive_info in dpu.drives:
                    self.drives.append(drive_info.uuid)
        self.drives.sort()
        fun_test.log(self.drives)
        self.storage_controller_template.initialize(already_deployed=False)

    def run(self):
        fs_obj_list = [self.topology.get_dut_instance(index=dut_index)
                       for dut_index in self.topology.get_available_duts().keys()]
        storage_controller = fs_obj_list[0].get_storage_controller()
        topology_result = storage_controller.topology_api.get_hierarchical_topology()
        fun_test.log(topology_result)
        drives2 = []
        for node in topology_result.data:
            for dpu in topology_result.data[node].dpus:
                for drive_info in dpu.drives:
                    drives2.append(drive_info.uuid)
        drives2.sort()
        fun_test.log("Drives before format: {}".format(self.drives))
        fun_test.log("Drives after format: {}".format(drives2))
        fun_test.test_assert(self.drives != drives2,
                             message="Comparing drive UUIDs after drive format")

    def cleanup(self):
        self.storage_controller_template.cleanup(fun_test.is_current_test_case_failed())


if __name__ == "__main__":
    setup_bringup = BootupSetup()
    setup_bringup.add_test_case(RunStorageApiCommands())
    setup_bringup.run()
