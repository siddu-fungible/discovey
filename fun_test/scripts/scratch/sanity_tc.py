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
        self.set_test_details(id="122",
                              summary="Sanity Test 1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        import time
        time.sleep(200)
        fun_test.add_checkpoint("Some checkpoint")
        for i in range(0, 50):
            fun_test.log("Some log")

        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id="$tc",
                              summary="Sanity Test 2",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        print("The Testcase")



        fun_test.test_assert(expression=1 > 2, message="1 > 2")
        fun_test.test_assert(expression=2 > 1, message="2 > 1")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.add_test_case(FunTestCase2(myscript))
    myscript.run()