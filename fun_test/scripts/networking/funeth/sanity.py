from lib.system.fun_test import *
from lib.host.linux import Linux
import re


class FunethScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. SN2 use cadence-pc-3 as NU host, and cadence-pc-5 as HU host
        2. In cadence-pc-3, configure interface fpg1
        3. In cadence-pc-5, load funeth driver, configure PF and VF interfaces, and run NU loopback test
        4. Test ping from cadence-pc-3 to cadence-pc-5 PF and VF - ping 53.1.1.5, ping 53.1.9.5
        """)

    def setup(self):

        # cadence-pc-3
        linux_obj = Linux(host_ip="cadence-pc-3", ssh_username="user", ssh_password="Precious1*")
        cmd = "/home/user/FunControlPlane/scripts/palladium_test/traffic_server/change_intf_name"
        fun_test.test_assert(linux_obj.command(cmd), "Change interface name")
        cmd = "/home/user/gliang/configure_fpg1.sh"
        fun_test.test_assert(linux_obj.command(cmd), "Configure interface fpg1")

        # cadence-pc-5
        linux_obj = Linux(host_ip="cadence-pc-5", ssh_username="localadmin", ssh_password="Precious1*")
        cmd = "/home/localadmin/gliang/test_funeth.py --sriov 4 --nu_loopback --packets 100"
        output = linux_obj.command(cmd)
        fun_test.test_assert(re.search(r'100 packets transmitted, 100 received, 0% packet loss', output), "NU loopback")

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect to NU host cadence-pc-3 and ping HU host cadence-pc-5",
                              steps="""
        1. Ping PF interface 53.1.1.5
        2. Ping VF interface 53.1.9.5
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        linux_obj = Linux(host_ip="cadence-pc-3", ssh_username="user", ssh_password="Precious1*")
        fun_test.test_assert(linux_obj.ping("53.1.1.5"), "Ping PF interface success")
        fun_test.test_assert(linux_obj.ping("53.1.9.5"), "Ping VF interface success")


if __name__ == "__main__":
    myscript = FunethScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
