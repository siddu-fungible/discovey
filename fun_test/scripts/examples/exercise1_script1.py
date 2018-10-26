from lib.system.fun_test import *
import random

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Nothing to setup
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Increment a counter",
                              steps="""
Initialize a counter to 0
Increment the counter 50 times using a for loop. In the for loop use fun_test.log to print the current value of the counter
At the end of the for loop, use fun_test.test_assert_expected to report what is expected and actual
Ref: https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/examples/sanity.py . TestCase1
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        counter = 0
        num_iterations = 50
        for i in range(num_iterations):
            counter += 1
            fun_test.log("Current Value of counter: {}".format(counter))
        fun_test.test_assert_expected(expected=num_iterations, actual=counter, message="Counter Value")


class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Check if 100 random numbers generated in a loop are always < 50",
                              steps="""
                              Write a for loop, to generate 100 random numbers. A random number can be generated via 
import random
number = random.randint(0, 100)
Use fun_test.test_assert in the for loop to ensure that no number generated is less than 50. The test-case will stop if the assertion fails
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        fun_test.log("Generating random numbers")
        num_iterations = 100
        for i in range(num_iterations):
            random_number = random.randint(0, 100)
            fun_test.test_assert(random_number >= 50, "Random number {} is greater than 50.".format(random_number))


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.run()