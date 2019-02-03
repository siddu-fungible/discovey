from funeth import Funeth
from scripts.networking.tb_configs import tb_configs
from lib.system.fun_test import *


TB = 'SN2'


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
        fun_test.test_assert(funeth_obj.lspci(), 'Fungible Ethernet controller is seen.')
        fun_test.test_assert(funeth_obj.update_src(), 'Update funeth driver source code.')
        fun_test.test_assert(funeth_obj.build(), 'Build funeth driver.')
        fun_test.test_assert(funeth_obj.load(sriov=4), 'Load funeth driver.')
        fun_test.test_assert(funeth_obj.configure_intfs('hu'), 'Configure funeth interfaces.')
        fun_test.test_assert(funeth_obj.configure_ipv4_route('hu'), 'Configure HU host IPv4 routes.')
        fun_test.test_assert(funeth_obj.loopback_test(packet_count=100),
                             'HU PF and VF interface loopback ping test via NU')
        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        pass


class FunethTestNUPingHU(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="From NU host ping HU host.",
                              steps="""
        1. Ping PF interface, e.g. 53.1.1.5
        2. Ping VF interface, e.g. 53.1.9.5
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['nu']
        tb_config_obj = funeth_obj.tb_config_obj

        # PF
        pf_ip_addr = tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.pf_intf)
        fun_test.test_assert(linux_obj.ping(pf_ip_addr), "Ping PF interface success")

        # VF
        vf_ip_addr = tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf)
        fun_test.test_assert(linux_obj.ping(vf_ip_addr), "Ping VF interface success")


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
