from lib.system.fun_test import *
from lib.templates.storage.storage_template import StorageTemplate
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

    def cleanup(self):
        if "topology" in fun_test.shared_variables and fun_test.shared_variables["topology"]:
            fun_test.shared_variables["topology"].cleanup()


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create and attach namespace",
                              steps="""
        1. Create a namespace
        2. Attach a namespace
        3. Check if nvme0 is in the output of lsblk
        4. Ensure the type of the device is 'disk'
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        dut_instance = fun_test.shared_variables["topology"].get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance")
        storage_controller = StorageController(target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)

        result = storage_controller.ip_cfg(ip=dut_instance.host_ip)
        fun_test.test_assert(result["status"], "ip_cfg {}".format(dut_instance.data_plane_ip))

        this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
        result = storage_controller.create_thin_block_volume(capacity=1073741824,
                                                      block_size=4096,
                                                      name="volume1",
                                                      uuid=this_uuid)
        fun_test.test_assert(result["status"], "create_thin_block_volume")

        result = storage_controller.command("peek storage/volumes")
        i = 0
        # result = storage_controller.command("peek stats")
        # storage_controller.print_result(result)

if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
