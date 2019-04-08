
from lib.system.fun_test import *

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
                              summary="Sanity Test 1",
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
        fun_test.log("Some log: vanilla 2")
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")
        inputs = fun_test.get_job_inputs()
        if inputs:
            fun_test.log("Inputs: " + str(inputs))
        else:
            fun_test.log("No job inputs provided")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())

    myscript.run()
