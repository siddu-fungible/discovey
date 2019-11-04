
from lib.system.fun_test import *

i = 0
j = 0

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2 (a)
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
        fun_test.log("Version is: {}".format(fun_test.get_version()))

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.log("Some log: vanilla 2")
        banner = '<iframe width="420" height="345" src="https://www.youtube.com/embed/KNZSXnrbs_k"></iframe>'
        fun_test.set_suite_execution_banner(banner=banner)
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")

class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Sanity Test 2",
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

class FunTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Sanity Test 3",
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

class FunTestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Sanity Test 4",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Test-case setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Test-case cleanup")

    def run(self):
        fun_test.log("Some log: vanilla 2")
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.add_test_case(FunTestCase3())
    myscript.add_test_case(FunTestCase4())
    myscript.run()
