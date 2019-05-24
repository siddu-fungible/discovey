from lib.system.fun_test import *
from dateutil import parser

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
                              summary="Test 1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.log("Version is: {}".format(fun_test.get_version()))

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        result = fun_test.get_stored_enviroment_variable("test")
        fun_test.log("got the test variable that is already set {}".format(result))
        result = parser.parse(result)
        fun_test.log("converted to datetime object {}".format(result))


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()