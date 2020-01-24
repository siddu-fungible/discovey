from lib.system.fun_test import *
from lib.system import utils
from lib.host.linux import Linux
from lib.host.swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.host.swagger_client.models.body_volume_attach import BodyVolumeAttach
from lib.host.swagger_client.models.body_node_update import BodyNodeUpdate
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.templates.storage.review.storage_template import BltVolumeTemplate
from lib.host.swagger_client.models.volume_types import VolumeTypes


class BringupSetup(FunTestScript):

    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        already_deployed = True

        topology_helper = TopologyHelper()

        topology_helper.set_dut_parameters(fs_parameters={"already_deployed": already_deployed})

        self.topology = topology_helper.deploy()

        fun_test.test_assert(self.topology, "Topology deployed")

        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        self.topology.cleanup()


class RunStorageApiCommands(FunTestCase):
    topology = None

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
        compression_effort = False,
        encrypt = False
        attach_volume_map = {}
        # ask only for fs objects | fs_obj and host_obj variables consistency
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        # raise exception for deploy
        storage_controller_template = BltVolumeTemplate(topology=self.topology,
                                                        attach_volume_map=attach_volume_map)
        vol_uuid = storage_controller_template.create_volume(fs_obj)
        storage_controller_template.attach_volume(vol_uuid, fs_obj)

        for index in self.topology.get_duts().keys():
            fs = self.topology.get_dut_instance(index=index)
            attach_volume_map[fs] = []

            hosts = self.topology.get_hosts()
            host_instance_list = []
            for host in hosts:

                host_instance = hosts[host].get_instance()
                host_instance_list.append(host_instance)
            count += 0
            body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})

            attach_volume_map[fs].append({'host_list': host_instance_list,
                                          'body_volume_intent_create': body_volume_intent_create})

        storage_controller_template = BltVolumeTemplate(topology=self.topology,
                                                        attach_volume_map=attach_volume_map)
        storage_controller_template.deploy()

    def run(self):
        pass
        Linux.nvme_connect()

    def cleanup(self):
        pass


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RunStorageApiCommands())
    setup_bringup.run()
