from lib.system.fun_test import *
from lib.templates.storage.storage_template import StorageTemplate
from lib.topology.topology_helper import TopologyHelper, Dut

# fun_test.enable_debug()



topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 2
                }
            },
            "simulation_start_mode": Dut.SIMULATION_START_MODE_NORMAL
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
        pass



if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.run()
