from lib.system.fun_test import *

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        pass

    def cleanup(self):
        pass

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
        fun_test.add_checkpoint("Some checkpoint")

        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")
        d = {

        }
        d[1] = "john"
        artifact_file_name = fun_test.create_test_case_artifact_file(post_fix_name="abc.json", contents=json.dumps(d))
        fun_test.set_topology_json_filename(artifact_file_name)

class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Sanity Test 2",
                              steps="Steps 1")

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.log("The Testcase")

        fun_test.test_assert(expression=1 > 2, message="1 > 2")
        fun_test.test_assert(expression=2 > 1, message="2 > 1")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.add_test_case(FunTestCase2(myscript))
    myscript.run()