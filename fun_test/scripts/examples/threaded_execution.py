from lib.system.fun_test import *


def some_func(a):
    fun_test.log("Time elapsed: {}".format(fun_test.get_wall_clock_time()))
    fun_test.log("Value: {}".format(a))
    fun_test.shared_variables["shared"] += 1
    fun_test.log("Shared variable = {}".format(fun_test.shared_variables["shared"]))


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Step 1
        2. Step 2""")

    def setup(self):
        fun_test.shared_variables["shared"] = 2

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Demo of calling a function as a thread",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        # Execute the function func as a thread after 5 seconds
        thread_id = fun_test.execute_thread_after(time_in_seconds=5, func=some_func, a=5)
        fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

        # Execute the function func after 5 seconds
        thread_id = fun_test.execute_after(time_in_seconds=5, func=some_func, a=6)
        fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())

    myscript.run()
