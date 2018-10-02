from lib.system.fun_test import *
from lib.host.linux import Linux


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
                              summary="Connect to qa-ubuntu-02 using Linux and ping 127.0.0.1",
                              steps="""
Use from lib.host.linux import Linux
Use the Linux class to instantiate an object, connect to qa-ubuntu-02 over ssh, and use Linux.ping to ping 127.0.0.1
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        linux_obj = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
        fun_test.test_assert(linux_obj.ping("127.0.0.1"), "Ping success")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()