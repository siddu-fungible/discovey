from lib.system.fun_test import *

class MyScript(FunTestScript):
    test_case_order = [
        {
            "tc": "FunTestCase2",
            "dependencies": []
        },
        {
            "tc": "FunTestCase1",
            "dependencies": ["FunTestCase3", "FunTestCase4"]
        }
    ]
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        pass

    def cleanup(self):
        pass

class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Description 1",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Some checkpoint")
        fun_test.test_assert_expected(expected=2, actual=2, message="Some bvjgfgjhjghfghfghfghjfgjhfghfjghfgjhfgjhfgjhfghjfgjhfghjfgjhfghjfjghfghjfhgjfghjfgjfgjhfmessage2")


class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Description 2",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        print("The Testcase")
        fun_test.test_assert(expression=2 > 1, message="2 > 1")

class FunTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Description 3",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        print("The Testcase")
        fun_test.test_assert(expression=2 > 1, message="2 > 1")


class FunTestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Description 4",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        print("The Testcase")
        fun_test.test_assert(expression=2 > 1, message="2 > 1")





if __name__ == "__main__":
    fun_test.test(__file__)
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.add_test_case(FunTestCase3())
    myscript.add_test_case(FunTestCase4())

    myscript.run()
