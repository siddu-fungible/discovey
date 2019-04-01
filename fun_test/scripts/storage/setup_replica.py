from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.storage_controller import StorageController
from lib.fun.f1 import F1
import uuid
# fun_test.enable_debug()
# fun_test.enable_pause_on_failure()


topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        },
        1: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        },
        2: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }
    }

}

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and Allocate a QEMU instance
        2. Make the QEMU instance available for the testcase
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")

        fun_test.shared_variables["topology"] = topology
        # topology_obj_helper.save(file_name="mypickle.pkl") # Useful when you do not recreate topologies/containers during development
        #                                                   # Use the complement function .load() to retrieve the topology
        pass

    def cleanup(self):
        if "topology" in fun_test.shared_variables:
            fun_test.shared_variables["topology"].cleanup()
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Setting up a replica",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
           a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
           b. Attach a replica volume using the 2 volumes imported at step a. 
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        # topology = TopologyHelper().load("mypickle.pkl") # To be used only in association with .load()

        topology = fun_test.shared_variables["topology"]
        dut_instance0 = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance0, "Retrieved dut instance 0")

        dut_instance1 = topology.get_dut_instance(index=1)
        fun_test.test_assert(dut_instance1, "Retrieved dut instance 1")

        dut_instance2 = topology.get_dut_instance(index=2)
        fun_test.test_assert(dut_instance2, "Retrieved dut instance 2")

        created_uuids = []
        ns_id = 1
        capacity = 1073741824
        block_size = 4096
        volume_name = "volume1"

        for index, dut_instance in enumerate([dut_instance0, dut_instance1]):
            storage_controller = StorageController(target_ip=dut_instance.host_ip,
                                                   target_port=dut_instance.external_dpcsh_port)

            result = storage_controller.ip_cfg(ip=dut_instance.data_plane_ip)
            fun_test.test_assert(result["status"], "ip_cfg {} on Dut Instance {}".format(dut_instance.data_plane_ip, index))

            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            created_uuids.append(this_uuid)
            result = storage_controller.create_thin_block_volume(capacity=capacity,
                                                          block_size=block_size,
                                                          name=volume_name,
                                                          uuid=this_uuid)
            fun_test.test_assert(result["status"], "create_thin_block_volume on Dut Instance {}".format(index))
            result = storage_controller.volume_attach_remote(ns_id=ns_id, uuid=this_uuid, remote_ip=dut_instance2.data_plane_ip)
            fun_test.test_assert(result["status"], "attach volume on Dut Instance {}".format(index))

        fun_test.add_checkpoint("Importing volumes on index 2")
        storage_controller = StorageController(target_ip=dut_instance2.host_ip,
                                               target_port=dut_instance2.external_dpcsh_port)
        result = storage_controller.ip_cfg(ip=dut_instance2.data_plane_ip)
        fun_test.test_assert(result["status"], "ip_cfg {} on Dut Instance {}".format(dut_instance2.data_plane_ip, 2))

        rds_uuids = []
        for index, dut_instance in enumerate([dut_instance0, dut_instance1]):
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            rds_uuids.append(this_uuid)
            result = storage_controller.create_rds_volume(capacity=capacity,
                                                          block_size=block_size,
                                                          name=volume_name,
                                                          uuid=this_uuid,
                                                          remote_nsid=ns_id,
                                                          remote_ip=dut_instance.data_plane_ip)
            fun_test.test_assert(result["status"], "Create RDS volume for index: {}".format(index))

        this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
        result = storage_controller.create_replica_volume(capacity=capacity,
                                                          uuid=this_uuid,
                                                          block_size=block_size,
                                                          name=volume_name,
                                                          pvol_id=rds_uuids)
        fun_test.test_assert(result["status"], "Create Replica volume on index: {}".format(2))

        result = storage_controller.peek(props_tree="storage/volumes")
        fun_test.simple_assert(result["status"], "Peeking storage volume stats")
        fun_test.test_assert_expected(actual=len(result["data"]["VOL_TYPE_BLK_RDS"].keys()),
                                      expected=len(rds_uuids), message="Ensure RDS volumes are found ")
        fun_test.test_assert_expected(actual=len(result["data"]["VOL_TYPE_BLK_REPLICA"].keys()),
                                      expected=1, message="Ensure Replica volumes are found ")


if __name__ == "__main__":

    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
