from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time

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
        self.db_log_time = get_data_collection_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        date_time = fun_test.shared_variables["db_log_time"]
        fun_test.log("date_time is {}".format(date_time))
        fun_test.log("updated the test variable with value {}".format(date_time))


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()