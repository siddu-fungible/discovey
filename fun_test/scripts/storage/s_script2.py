from lib.system.fun_test import *
from lib.host.linux import Linux


class MyScript(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                              """)
    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1, summary="Description 1", steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        linux_obj = Linux(host_ip="10.1.20.67",
                          ssh_username="root",
                          ssh_password="fun123")

        linux_obj.trace(id="Linux1", enable=True)
        for i in range(0, 5):
            linux_obj.command("date")
        fun_test.test_assert_expected(expected=5, actual=5, message="Silly comparison")

        linux_obj = Linux(host_ip="10.1.20.67",
                          ssh_username="root",
                          ssh_password="fun123")


        linux_obj.trace(id="Linux2", enable=True)
        linux_obj.command("ls")
        fun_test.test_assert_expected(expected=5, actual=5, message="Silly comparison2")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.run()
