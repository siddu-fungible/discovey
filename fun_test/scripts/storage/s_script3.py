from lib.system.fun_test import *
from lib.fun.f1 import F1
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
                    "hosts": 0
                }
            },
            "simulation_start_mode": Dut.SIMULATION_START_MODE_DPCSH_ONLY
        }

    }
}


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                              """)

    def setup(self):
        self.topology_obj = TopologyHelper(spec=topology_dict).deploy()

        fun_test.test_assert(self.topology_obj, "Successfully deployed topology")

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Demo ikv create using dpcsh",
                              steps="""
        1. Start FunOs with dpcsh
        2. Start dpcsh
        3. Use dpcsh to do ikv create
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        f1_obj = self.script_obj.topology_obj.get_dut_instance(index=0)
        f1_obj.trace(id="F1 dpcsh", enable=True)

        dpcsh_output = f1_obj.dpcsh_command(r'ikvdemo create_and_open {size_param: "small"}')
        fun_test.test_assert(dpcsh_output, "Ensure dpcsh output could be parsed")

        dpcsh_output = f1_obj.dpcsh_command(r'ikvdemo put {"ikv_container": %d} [123456789]' % (dpcsh_output['ikv_container']))
        fun_test.test_assert(dpcsh_output, "Ensure put operation is successful")


        f1_obj.disconnect()



if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.run()
