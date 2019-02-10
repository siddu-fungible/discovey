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
        funeth_obj.setup_workspace()

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
        fun_test.shared_variables['funeth_obj'].cleanup_workspace()


def verify_nu_hu_datapath(funeth_obj):
    linux_obj = funeth_obj.linux_obj_dict['nu']
    tb_config_obj = funeth_obj.tb_config_obj

    interfaces = tb_config_obj.get_all_interfaces('hu')
    ip_addrs = [tb_config_obj.get_interface_ipv4_addr('hu', intf) for intf in interfaces]

    for intf, ip_addr in zip(interfaces, ip_addrs):
        fun_test.test_assert(linux_obj.ping(ip_addr, max_percentage_loss=0, interval=0.01, sudo=True),
                             'NU ping HU interfaces {}'.format(intf))


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
        verify_nu_hu_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'])


class FunethTestPacketSweep(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
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


class FunethTestScpNU2HUPF(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Scp a file from NU to HU host via PF.",
                              steps="""
        1. 
        """)

    def setup(self):
        linux_obj = fun_test.shared_variables['funeth_obj'].linux_obj_dict['nu']
        self.file_name = '/tmp/nufile'

        # Create a file
        if TB == 'SN2':
            file_size = '2m'
        elif TB == 'SB5':
            file_size = '2g'
        linux_obj.command('xfs_mkfile {} {}'.format(file_size, self.file_name))

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['nu']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        fun_test.test_assert(
            linux_obj.scp(source_file_path=self.file_name,
                          target_ip=tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.pf_intf),
                          target_file_path='/tmp/nufilepf',
                          target_username=tb_config_obj.get_username('hu'),
                          target_password=tb_config_obj.get_password('hu')),
            'Scp a file from NU to HU host via PF.')


class FunethTestScpNU2HUVF(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Scp a file from NU to HU host via VF.",
                              steps="""
        1. 
        """)

    def setup(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['nu']
        tb_config_obj = funeth_obj.tb_config_obj

        # Create a file
        self.file_name = '/tmp/nufile'
        if TB == 'SN2':
            file_size = '2m'
        elif TB == 'SB5':
            file_size = '2g'
        linux_obj.command('xfs_mkfile {} {}'.format(file_size, self.file_name))

        # Start sshd in VF namespace
        ns = tb_config_obj.get_hu_pf_namespace()
        if ns != 'default':
            linux_obj = funeth_obj.linux_obj_dict['hu']
            linux_obj.command('sudo ip netns exec {} /usr/sbin/sshd &'.format(ns))

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['nu']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        fun_test.test_assert(
            linux_obj.scp(source_file_path=self.file_name,
                          target_ip=tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf),
                          target_file_path='/tmp/nufilevf',
                          target_username=tb_config_obj.get_username('hu'),
                          target_password=tb_config_obj.get_password('hu')),
            'Scp a file from NU to HU host via VF.')


class FunethTestScpHU2NU(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Scp a file from HU to NU host.",
                              steps="""
        1. 
        """)

    def setup(self):
        linux_obj = fun_test.shared_variables['funeth_obj'].linux_obj_dict['hu']
        self.file_name = '/tmp/hufile'

        # Create a file
        if TB == 'SN2':
            file_size = '2m'
        elif TB == 'SB5':
            file_size = '2g'
        linux_obj.command('xfs_mkfile {} {}'.format(file_size, self.file_name))

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['hu']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj
        fun_test.test_assert(
            linux_obj.scp(source_file_path=self.file_name,
                          target_ip=tb_config_obj.get_interface_ipv4_addr('nu', tb_config_obj.get_a_nu_interface()),
                          target_file_path='/tmp',
                          target_username=tb_config_obj.get_username('nu'),
                          target_password=tb_config_obj.get_password('nu')),
            'Scp a file from HU to NU host.')


class FunethTestInterfaceFlap(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
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
        self.set_test_details(id=7,
                              summary="Unload funeth driver and reload it.",
                              steps="""
        1. 
        """)

    def setup(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']

        # Unload driver
        fun_test.test_assert(funeth_obj.unload(), 'Unload funeth driver.')

        # Load driver and configure
        fun_test.test_assert(funeth_obj.load(sriov=4), 'Load funeth driver.')
        fun_test.test_assert(funeth_obj.configure_intfs('hu'), 'Configure funeth interfaces.')
        fun_test.test_assert(funeth_obj.configure_ipv4_route('hu'), 'Configure HU host IPv4 routes.')
        fun_test.test_assert(funeth_obj.loopback_test(packet_count=100),
                             'HU PF and VF interface loopback ping test via NU')

    def cleanup(self):
        pass

    def run(self):
        verify_nu_hu_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'])


if __name__ == "__main__":
    ts = FunethSanity()
    for tc in (
            FunethTestNUPingHU,
            #FunethTestPacketSweep,
            #FunethTestScpNU2HUPF,
            #FunethTestScpNU2HUVF,
            #FunethTestScpHU2NU,
            #FunethTestInterfaceFlap,
            FunethTestUnloadDriver,
    ):
        ts.add_test_case(tc())
    ts.run()

