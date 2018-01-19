from lib.host.traffic_generator import TrafficGenerator
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
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_FIO
        }
    }
}

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy multiple containers with F1 
        2. Deploy one container with a traffic generator
        3. Start the F1s in dpc-server mode
                              """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict) use locally defined dictionary variable
        topology_obj_helper = TopologyHelper(spec_file="./multiple_f1s_w_repeat.json")
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Use StorageController",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy for each of the 3 F1s
        2. Configure ip_cfg 
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        topology = fun_test.shared_variables["topology"]
        dut_instance0 = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance0, "Retrieved dut instance 0")

        dut_instance1 = topology.get_dut_instance(index=1)
        fun_test.test_assert(dut_instance1, "Retrieved dut instance 1")

        dut_instance2 = topology.get_dut_instance(index=2)
        fun_test.test_assert(dut_instance2, "Retrieved dut instance 2")


        for index, dut_instance in enumerate([dut_instance0, dut_instance1]):
            storage_controller = StorageController(target_ip=dut_instance.host_ip,
                                                   target_port=dut_instance.external_dpcsh_port)

            result = storage_controller.ip_cfg(ip=dut_instance.data_plane_ip)
            fun_test.test_assert(result["status"], "ip_cfg {} on Dut Instance {}".format(dut_instance.data_plane_ip, index))


        fio = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance2.data_plane_ip
        fio.send_traffic(destination_ip=destination_ip)



if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
