from lib.system.fun_test import *
from lib.templates.storage.storage_template import StorageTemplate
from lib.topology.topology_helper import TopologyHelper, Dut
from lib.host.storage_controller import StorageController
import uuid
# fun_test.enable_debug()



topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": Dut.DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "simulation_start_mode": Dut.SIMULATION_START_MODE_DPCSH_ONLY
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
        self.topology = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")

    def cleanup(self):
        pass


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
        dut_instance = self.script_obj.topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance")
        storage_controller = StorageController(mode="ikvdemo",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)

        d = {"size_param": "small"}
        action = "create_and_open"
        result = storage_controller.json_command(data=d, action="create_and_open")
        fun_test.test_assert(result["status"], action)

        ikv_container_id = result["data"]["ikv_container"]

        # d = {"ikv_container": ikv_container_id}
        # result = storage_controller.json_command(data=d, action="put", additional_info="[123456789]")
        # fun_test.test_assert(result["status"], "Ensure put operation is successful")


        result = storage_controller.command("peek storage/volumes")

if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.run()
