from lib.system.fun_test import *
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
                    "hosts": 1
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
        self.topology_obj = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology_obj, "Ensure deploy is successful")

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
        host = self.script_obj.topology_obj.get_host_instance(dut_index=0, interface_index=0)  # First QEMU instance
        host.trace(id="Linux", enable=True)

        host.command("lsblk")

        device = "/dev/nvme0"
        namespace_id = 1
        controllers = 1

        fun_test.test_assert(host.nvme_create_namespace(size=32768,
                                                           capacity=32768,
                                                           device=device),
                                "Create Namespace")
        fun_test.sleep("Create Namespace", 10)
        fun_test.test_assert(host.nvme_attach_namespace(namespace_id=namespace_id,
                                                           controllers=controllers,
                                                           device=device),
                                "Attach Namespace")
        fun_test.sleep("Attach Namespace", 10)

        lsblk = host.lsblk()
        expected_name = device.replace("/dev/", "") + "n" + str(namespace_id)
        fun_test.test_assert(expected_name in lsblk, "Check if {} is in lsblk".format(expected_name))
        fun_test.test_assert_expected(expected="disk",
                                         actual=lsblk[expected_name]["type"],
                                         message="Type should be disk")

class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Description 1",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        print("The Testcase")


if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.add_test_case(FunTestCase2(myscript))
    myscript.run()
