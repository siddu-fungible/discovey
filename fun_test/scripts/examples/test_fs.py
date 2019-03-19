from lib.system.fun_test import *
from lib.fun.fs import Fs

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

    def run(self):
        fs_json = ASSET_DIR + "/fs.json"
        json_spec = parse_file_to_json(file_name=fs_json)
        fs = Fs.get(spec=json_spec[0])
        fun_test.test_assert(fs.bootup(reboot_bmc=True), "FS bootup")



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
