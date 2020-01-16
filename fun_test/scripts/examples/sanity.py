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
        fun_test.shared_variables["some_variable"] = 123

    def cleanup(self):
        fun_test.log("Script-level cleanup")

class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity Test 1",
                              test_rail_case_ids=["C19878"],
                              steps=""",
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
        for i in range(0, 500):
            fun_test.log("Some log")

        fun_test.log("Variable shared across test-cases and the script level: {}".format(fun_test.shared_variables["some_variable"]))


        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


class FunTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
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
        for i in range(0, 500):
            fun_test.log("Some log")

        fun_test.log("Variable shared across test-cases and the script level: {}".format(fun_test.shared_variables["some_variable"]))


        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


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


class FunTestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
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
        for i in range(0, 500):
            fun_test.log("Some log")

        fun_test.log("Variable shared across test-cases and the script level: {}".format(fun_test.shared_variables["some_variable"]))


        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.add_test_case(FunTestCase3())
    myscript.add_test_case(FunTestCase4())

    myscript.run()
