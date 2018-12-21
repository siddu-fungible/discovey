from lib.system.fun_test import *
from lib.host.linux import Linux
import re


NU_HOST = 'cadence-pc-3'
HU_HOST = 'cadence-pc-5'
NU_INTF = 'fpg0'
NU_HOST_FPG0_IP_ADDR = '19.1.1.1'
NU_HOST_FPG0_IP_NETMASK = '255.255.255.0'
NU_HOST_FPG0_MAC_ADDR = 'fe:dc:ba:44:66:33'
NU_ROUTE_TO_HU_PF = '53.1.1.0/24'
NU_ROUTE_TO_HU_VF = '53.1.9.0/24'
NU_ROUTE_NEXTHOP = '19.1.1.2'


class FunethSanity(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU host, configure interface fpg1 and routes to HU host
        2. In HU host, load funeth driver, configure PF and VF interfaces, and run NU loopback test
        3. In HU host, configure route to NU host
        4. Test ping from NU host to HU host PF and VF - ping 53.1.1.5, ping 53.1.9.5
        """)

    def setup(self):

        # NU host
        linux_obj = Linux(host_ip=NU_HOST, ssh_username="user", ssh_password="Precious1*")
        linux_obj.command("/home/user/FunControlPlane/scripts/palladium_test/traffic_server/change_intf_name")
        linux_obj.command("/home/user/gliang/configure_fpg0.sh")
        output = linux_obj.command('ifconfig %s' % NU_INTF)
        fun_test.test_assert(
            re.search(r'%s.*%s.*%s' % (NU_HOST_FPG0_IP_ADDR, NU_HOST_FPG0_IP_NETMASK, NU_HOST_FPG0_MAC_ADDR), output,
                      re.DOTALL) is not None,
            "Configure interface fpg0")
        output = linux_obj.command('ip route')
        fun_test.test_assert(
            re.search('%s via %s dev %s' % (NU_ROUTE_TO_HU_PF, NU_ROUTE_NEXTHOP, NU_INTF), output) is not None,
            "Configure ip route to HU host PF interface")
        fun_test.test_assert(
            re.search('%s via %s dev %s' % (NU_ROUTE_TO_HU_VF, NU_ROUTE_NEXTHOP, NU_INTF), output) is not None,
            "Configure ip route to HU host VF interface")
        fun_test.shared_variables['nu_linux_obj'] = linux_obj

        # HU host
        linux_obj = Linux(host_ip=HU_HOST, ssh_username="localadmin", ssh_password="Precious1*")
        cmd = "/home/localadmin/gliang/test_funeth.py --sriov 4 --nu_loopback --packets 100"
        output = linux_obj.command(cmd, timeout=300)
        fun_test.test_assert(
            re.search(r'100 packets transmitted, 100 received, 0% packet loss', output),
            "HU PF and VF interface loopback ping test via NU")
        linux_obj.command('/home/localadmin/gliang/hu.sh')
        fun_test.shared_variables['hu_linux_obj'] = linux_obj


    def cleanup(self):
        pass


class FunethTestNUPingHU(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect to NU host NU host and ping HU host HU host",
                              steps="""
        1. Ping PF interface 53.1.1.5
        2. Ping VF interface 53.1.9.5
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        linux_obj = fun_test.shared_variables['nu_linux_obj']
        fun_test.test_assert(linux_obj.ping("53.1.1.5"), "Ping PF interface success")
        fun_test.test_assert(linux_obj.ping("53.1.9.5"), "Ping VF interface success")


if __name__ == "__main__":
    FunethScript = FunethSanity()
    FunethScript.add_test_case(FunethTestNUPingHU())
    FunethScript.run()
