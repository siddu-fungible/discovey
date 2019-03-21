from lib.system.fun_test import *
from lib.fun.fs import Fs
from asset.asset_manager import AssetManager

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
                              summary="Setup FS1600",
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
        fun_test.shared_variables["fs"].cleanup()

    def run(self):
        fs = Fs.get()
        fun_test.shared_variables["fs"] = fs
        fun_test.test_assert(fs.bootup(reboot_bmc=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        f1.get_dpc_client().json_execute(verb="peek", data="stats/vppkts", command_duration=4)



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
