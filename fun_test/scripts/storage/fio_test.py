from lib.host.traffic_generator import TrafficGenerator
from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper

# fun_test.enable_debug()
# fun_test.enable_pause_on_failure()


topology_dict = {
    "name": "Basic Storage",
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_FIO
        }
    }
}

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. 
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="FIO tests",
                              steps="""
        1.Steps
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        pass

if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
