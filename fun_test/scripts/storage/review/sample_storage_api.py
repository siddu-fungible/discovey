from lib.system.fun_test import *
from lib.system import utils
from lib.host.linux import Linux
from lib.host.swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.review.storage_template import BltVolumeTemplate
from lib.host.swagger_client.models.volume_types import VolumeTypes


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
        attach_volume_map = {}
        # ask only for fs objects | fs_obj and host_obj variables consistency
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        # raise exception for deploy
        self.storage_controller_template = BltVolumeTemplate(topology=self.topology)
        self.storage_controller_template.initialize()

        fs_obj_list = []
        for index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=index)
            fs_obj_list.append(fs_obj)

        vol_uuid_dict = self.storage_controller_template.create_volume(fs_obj_list=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)

        hosts = self.topology.get_hosts()
        for fs_obj in vol_uuid_dict:
            for host_id in hosts:
                host_obj = hosts[host_id]
                attach_vol_res = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=fs_obj,
                                                                                volume_uuid=vol_uuid_dict[fs_obj])

                self.storage_controller_template.nvme_connect_from_host(host_obj=host_obj,
                                                                        subsys_nqn=attach_vol_res.subsys_nqn,
                                                                        host_nqn=attach_vol_res.host_nqn,
                                                                        dataplane_ip=attach_vol_res.ip)

    def run(self):
        pass

    def cleanup(self):
        self.storage_controller_template.cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RunStorageApiCommands())
    setup_bringup.run()
