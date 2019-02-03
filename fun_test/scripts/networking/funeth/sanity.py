from funeth import Funeth
from tb_configs import tb_configs
from lib.system.fun_test import *
from lib.host.linux import Linux
import re


TB = 'SN2'

NU_HOST = 'cadence-pc-3'
HU_HOST = 'cadence-pc-5'
NU_INTF = 'fpg0'
NU_HOST_FPG0_IP_ADDR = '19.1.1.1'
NU_HOST_FPG0_IP_NETMASK = '255.255.255.0'
NU_HOST_FPG0_MAC_ADDR = 'fe:dc:ba:44:66:33'
NU_ROUTE_TO_HU_PF = '53.1.1.0/24'
NU_ROUTE_TO_HU_VF = '53.1.9.0/24'
NU_ROUTE_NEXTHOP = '19.1.1.2'
ROUTER_MAC = '00:de:ad:be:ef:00'


class FunethSanity(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU host, configure fpg interface and routes to HU host
        2. In HU host, load funeth driver, configure PF and VF interfaces, and run NU loopback test
        3. In HU host, configure route to NU host
        4. Test ping from NU host to HU host PF and VF - e.g. ping 53.1.1.5, ping 53.1.9.5
        """)

    def setup(self):

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = Funeth(tb_config_obj)

        # NU host
        fun_test.test_assert(funeth_obj.configure_intfs('nu'), 'Configure NU host interface')
        fun_test.test_assert(funeth_obj.configure_ipv4_route('nu'), 'Configure NU host IPv4 routes')

        # HU host
        fun_test.test_assert(
            re.search(r'Ethernet controller: (?:Device 1dad:1000|Fungible Device 1000)', funeth_obj.lspci()),
            'Fungible Ethernet controller is seen.')
        fun_test.test_assert(
            re.search(r'Updating working projectdb.*Updating current build number', funeth_obj.update_src(), re.DOTALL),
            'Update funeth driver source code.')
        fun_test.test_assert(
            not re.search(r'fail|error|abort|assert', funeth_obj.build(), re.IGNORECASE),
            'Build funeth driver.')
        fun_test.test_assert(
            not re.search(r'Device not found', funeth_obj.load(sriov=4), re.IGNORECASE),
            'Load funeth driver.')
        fun_test.test_assert(
            re.search(r'inet \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', funeth_obj.configure_intfs('hu')),
            'Configure funeth interfaces.')
        packet_count = 100
        output = funeth_obj.loopback_test(packet_count=packet_count)
        fun_test.test_assert(
            re.search(r'{0} packets transmitted, {0} received, 0% packet loss'.format(packet_count), output),
            "HU PF and VF interface loopback ping test via NU")
        fun_test.test_assert(funeth_obj.configure_ipv4_route('hu'), 'Configure IP routes to NU.')
        fun_test.shared_variables['hu_linux_obj'] = linux_obj
        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        pass


class FunethTestNUPingHU(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="From NU host ping HU host.",
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
        #fun_test.test_assert(linux_obj.ping("53.1.9.5"), "Ping VF interface success")


class FunethTestPacketSweep(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="From HU host, ping NU host with all available packet sizes.",
                              steps="""
        1. 
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        pass


class FunethTestInterfaceFlap(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Shut and no shut funeth interface.",
                              steps="""
        1. 
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        pass


class FunethTestUnloadDriver(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Unload funeth driver and reload it.",
                              steps="""
        1. 
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        pass


if __name__ == "__main__":
    FunethScript = FunethSanity()
    FunethScript.add_test_case(FunethTestNUPingHU())
    FunethScript.run()
