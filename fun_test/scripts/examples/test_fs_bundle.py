from lib.system.fun_test import *
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Setup FS standalone without TopologyHelper",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")
        # fun_test.shared_variables["fs"].cleanup()

    def run(self):
        fs = Fs.get(setup_bmc_support_files=True, boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog") # (disable_f1_index=0)
        fun_test.shared_variables["fs"] = fs
        fun_test.test_assert(fs.bootup(), "FS bootup")
        f1 = fs.get_f1(index=0)

        f1.get_dpc_client().json_execute(verb="peek", data="stats/vppkts", command_duration=4)
        fs.cleanup()

class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Setup FS standalone with TopologyHelper",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")
        # fun_test.shared_variables["fs"].cleanup()

    def run(self):
        # fun_test.build_parameters["bundle_image_parameters"] = {"release_train": "rel_1_0a_aa", "build_number": -1}
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0,
                                           custom_boot_args="app=load_mods --dpc-uart --dpc-server --all_100g",
                                           check_expected_containers_running=False)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        come = fs.get_come()
        come.setup_tools()
        #mfun_test.shared_variables["fs"] = fs
        topology.cleanup()

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase2())
    myscript.run()

