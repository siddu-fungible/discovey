from lib.system.fun_test import *
from fun_settings import SCRIPTS_DIR
from lib.host.linux import Linux
from lib.topology.topology_helper import TopologyHelper
from lib.host.network_controller import NetworkController
from lib.utilities.funcp_config import FunControlPlaneBringup
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs

import re


try:
    job_environment = fun_test.get_job_environment()
    DPC_PROXY_IP = str(job_environment['UART_HOST'])
    DPC_PROXY_PORT = int(job_environment['UART_TCP_PORT_0'])
    emulation_target = str(job_environment['EMULATION_TARGET']).lower()
    if emulation_target == 'palladium':
        TB = 'SN2'
    elif emulation_target == 'f1':
        if str(job_environment['HARDWARE_MODEL']) == 'F1Endpoint':
            TB = 'FS5'
        else:
            TB = 'SB5'
except (KeyError, ValueError):
    emulation_target = 'f1'
    #DPC_PROXY_IP = '10.1.21.120'
    #DPC_PROXY_PORT = 40221
    #TB = 'SN2'
    #DPC_PROXY_IP = '10.1.40.24'
    #DPC_PROXY_PORT = 40221
    #TB = 'SB5'
    DPC_PROXY_IP = '10.1.20.137'
    DPC_PROXY_PORT = 40220
    DPC_PROXY_IP2 = '10.1.20.137'
    DPC_PROXY_PORT2 = 40221
    TB = 'FS11'

# Enable LSO or not
try:
    inputs = fun_test.get_job_inputs()
    if inputs:
        enable_tso = (inputs.get('lso', 1) == 1)
    else:
        enable_tso = True
except:
    enable_tso = True

# Use control plane or not
try:
    inputs = fun_test.get_job_inputs()
    if inputs:
        control_plane = (inputs.get('control_plane', 0) == 1)
    else:
        control_plane = False
except:
    control_plane = False

# Update driver or not
try:
    inputs = fun_test.get_job_inputs()
    if inputs:
        update_driver = (inputs.get('update_driver', 1) == 1)
    else:
        update_driver = True
except:
    update_driver = True


MAX_MTU = 9000  # TODO: check SWLINUX-290 and update


def setup_nu_host(funeth_obj):
    if TB in ('FS7', 'FS11'):
        for nu in funeth_obj.nu_hosts:
            linux_obj = funeth_obj.linux_obj_dict[nu]
            fun_test.test_assert(linux_obj.reboot(non_blocking=True), 'NU host {} reboot'.format(linux_obj.host_ip))
        fun_test.sleep("Sleeping for the host to come up from reboot", seconds=30)
    for nu in funeth_obj.nu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[nu]
        #if TB in ('FS7', 'FS11'):
            #fun_test.test_assert(linux_obj.reboot(timeout=60, retries=5), 'Reboot NU host')
        fun_test.test_assert(linux_obj.is_host_up(), 'NU host {} is up'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_interfaces(nu), 'Configure NU host {} interface'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(nu), 'Configure NU host {} IPv4 routes'.format(
            linux_obj.host_ip))


def setup_hu_host(funeth_obj, update_driver=True):
    funsdk_commit = funsdk_bld = driver_commit = driver_bld = None
    if update_driver:
        funeth_obj.setup_workspace()
        fun_test.test_assert(funeth_obj.lspci(check_pcie_width=True), 'Fungible Ethernet controller is seen.')
        update_src_result = funeth_obj.update_src(parallel=True)
        if update_src_result:
            funsdk_commit, funsdk_bld, driver_commit, driver_bld = update_src_result
        fun_test.test_assert(update_src_result, 'Update funeth driver source code.')
    fun_test.test_assert(funeth_obj.build(parallel=True), 'Build funeth driver.')
    fun_test.test_assert(funeth_obj.load(sriov=4), 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]
        if enable_tso:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=False),
                                 'Enable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))
        else:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=True),
                                 'Disable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.enable_multi_txq(hu, num_queues=8),
                             'Enable HU host {} funeth interfaces multi Tx queues: 8.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(hu), 'Configure HU host {} IPv4 routes.'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_arps(hu), 'Configure HU host {} ARP entries.'.format(
            linux_obj.host_ip))
        #fun_test.test_assert(funeth_obj.loopback_test(packet_count=80),
        #                    'HU PF and VF interface loopback ping test via NU')

    return funsdk_commit, funsdk_bld, driver_commit, driver_bld


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

        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        fun_test.shared_variables["test_bed_type"] = test_bed_type

        # Boot up FS1600
        if test_bed_type == 'fs-11':

            if control_plane:
                f1_0_boot_args = "app=hw_hsu_test cc_huid=3 sku=SKU_FS1600_0 retimer=0,1 --all_100g --dpc-uart --dpc-server"
                f1_1_boot_args = "app=hw_hsu_test cc_huid=2 sku=SKU_FS1600_1 retimer=0,1 --all_100g --dpc-uart --dpc-server"
                topology_helper = TopologyHelper()
                topology_helper.set_dut_parameters(dut_index=0,
                                                   f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                                  1: {"boot_args": f1_1_boot_args}}
                                                   )
            else:
                boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g"
                topology_helper = TopologyHelper()
                topology_helper.set_dut_parameters(dut_index=0,
                                                   custom_boot_args=boot_args)

            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")
            fs = topology.get_dut_instance(index=0)

            come = fs.get_come()
            global DPC_PROXY_IP
            global DPC_PROXY_PORT
            DPC_PROXY_IP = come.host_ip
            fun_test.shared_variables["come_ip"] = come.host_ip
            DPC_PROXY_PORT = come.get_dpc_port(0)
            DPC_PROXY_PORT2 = come.get_dpc_port(1)

        if test_bed_type == 'fs-11' and control_plane:
            funcp_obj = FunControlPlaneBringup(fs_name="fs-11")
            funcp_obj.bringup_funcp(prepare_docker=False)
            funcp_obj.assign_mpg_ips_dhcp()
            abstract_json_file_f1_0 = '{}/networking/tb_configs/FS11_F1_0.json'.format(SCRIPTS_DIR)
            abstract_json_file_f1_1 = '{}/networking/tb_configs/FS11_F1_1.json'.format(SCRIPTS_DIR)
            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file_f1_0,
                                            abstract_config_f1_1=abstract_json_file_f1_1)
            fun_test.sleep("Sleeping for a while waiting for control plane to converge", seconds=10)
            # TODO: sanity check of control plane

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj

        # NU host
        if not control_plane:
            setup_nu_host(funeth_obj)

        # HU host
        self.funsdk_commit, self.funsdk_bld, self.driver_commit, self.driver_bld = setup_hu_host(
            funeth_obj, update_driver=update_driver)

        # TODO: remove below workaround after SWLINUX-729 is fixed
        #if test_bed_type == 'fs-11' and control_plane:
        #    funeth_obj.linux_obj_dict['hu'].command('ping 53.1.1.253 -c 1')
        #    funeth_obj.linux_obj_dict['hu2'].command('ping 53.1.1.253 -c 1')
        #    funeth_obj.linux_obj_dict['hu3'].command('ping 54.1.1.253 -c 1')
        #    funeth_obj.linux_obj_dict['hu4'].command('ping 54.1.1.253 -c 1')

        network_controller_obj = NetworkController(dpc_server_ip=DPC_PROXY_IP, dpc_server_port=DPC_PROXY_PORT,
                                                   verbose=True)
        fun_test.shared_variables['network_controller_obj'] = network_controller_obj

    def cleanup(self):
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fun_test.shared_variables["fs"].cleanup()
        elif fun_test.get_job_environment_variable('test_bed_type') == 'fs-11':
            fun_test.shared_variables["topology"].cleanup()
        funeth_obj = fun_test.shared_variables['funeth_obj']
        funeth_obj.cleanup_workspace()
        fun_test.log("Collect syslog from HU hosts")
        funeth_obj.collect_syslog()
        fun_test.log("Collect dmesg from HU hosts")
        funeth_obj.collect_dmesg()
        fun_test.test_assert(funeth_obj.unload(), 'Unload funeth driver')

        # TODO: Clean up control plane
        if control_plane:
            linux_obj = Linux(host_ip=fun_test.shared_variables["come_ip"], ssh_username='fun', ssh_password='123')
            linux_obj.sudo_command('rmmod funeth')
            linux_obj.sudo_command('docker kill F1-0 F1-1')
            linux_obj.sudo_command('rm -fr /tmp/*')


def collect_stats():
    try:
        network_controller_obj = fun_test.shared_variables['network_controller_obj']
        network_controller_obj.peek_fpg_port_stats(port_num=0)
        network_controller_obj.peek_fpg_port_stats(port_num=1)
        network_controller_obj.peek_fpg_port_stats(port_num=4)
        network_controller_obj.peek_psw_global_stats()
        network_controller_obj.peek_vp_packets()
    except:
        pass


def verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[], nu='nu', hu='hu'):
    linux_obj = funeth_obj.linux_obj_dict[nu]
    tb_config_obj = funeth_obj.tb_config_obj

    interfaces = [i for i in tb_config_obj.get_all_interfaces(hu) if i not in interfaces_excludes]
    ip_addrs = [tb_config_obj.get_interface_ipv4_addr(hu, intf) for intf in interfaces]

    # Collect fpg, psw, vp stats before and after
    collect_stats()

    for intf, ip_addr in zip(interfaces, ip_addrs):
        result = linux_obj.ping(ip_addr, count=packet_count, max_percentage_loss=0, interval=0.1,
                                size=packet_size-20-8,  # IP header 20B, ICMP header 8B
                                sudo=True)
        collect_stats()
        fun_test.test_assert(
            result,
            'NU ping HU interfaces {} with {} packets and packet size {}B'.format(intf, packet_count, packet_size))


class FunethTestNUPingHU(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="From NU host ping HU host PF/VF interfaces.",
                              steps="""
        1. Ping PF interface, e.g. 53.1.1.5
        2. Ping VF interface, e.g. 53.1.9.5
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        verify_nu_hu_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'], nu=nu, hu=hu)


class FunethTestPacketSweep(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="From NU host ping HU host PF/VF interfaces with all supported packet sizes.",
                              steps="""
        1. Set NU host interface , HU host interface, and NU FPG interface MTU to max
        2. From NU host, ping HU host PF/VF intefaces with all packet size from min to max.
        """)

    def setup(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'

        # NU
        linux_obj = funeth_obj.linux_obj_dict[nu]
        hostname = tb_config_obj.get_hostname(nu)
        interface = tb_config_obj.get_a_nu_interface(nu)
        fun_test.test_assert(linux_obj.set_mtu(interface, MAX_MTU),
                             'Set NU host {} interface {} MTU to {}'.format(hostname, interface, MAX_MTU))

        # HU
        linux_obj = funeth_obj.linux_obj_dict[hu]
        hostname = tb_config_obj.get_hostname(hu)
        namespaces = [tb_config_obj.get_hu_pf_namespace(hu), tb_config_obj.get_hu_vf_namespace(hu)]
        interfaces = [tb_config_obj.get_hu_pf_interface(hu), tb_config_obj.get_hu_vf_interface(hu)]
        for namespace, interface in zip(namespaces, interfaces):
            ns = None if namespace == 'default' else namespace
            fun_test.test_assert(linux_obj.set_mtu(interface, MAX_MTU, ns=ns),
                                 'Set HU host {} interface {} MTU to {}'.format(hostname, interface, MAX_MTU))

        # FPG MTU
        network_controller_obj = fun_test.shared_variables['network_controller_obj']
        fpg_port_num = int(tb_config_obj.get_a_nu_interface(nu).lstrip('fpg'))
        fpg_mtu = MAX_MTU + 14 + 4  # For Ethernet frame
        fun_test.test_assert(network_controller_obj.set_port_mtu(fpg_port_num, fpg_mtu),
                             'Set NU interface fpg{} MTU to {}'.format(fpg_port_num, fpg_mtu))

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        #for i in range(46, MAX_MTU+1):  # 64 - 14 - 4 = 46
        #    verify_nu_hu_datapath(funeth_obj, packet_count=2, packet_size=i)
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        linux_obj = funeth_obj.linux_obj_dict[nu]
        tb_config_obj = funeth_obj.tb_config_obj



        if emulation_target == 'palladium':  # Use only one PF and one VF interface to save run time
            interfaces = [tb_config_obj.get_hu_pf_interface(hu), tb_config_obj.get_hu_vf_interface(hu)]
        else:
            interfaces = tb_config_obj.get_all_interfaces(hu)
        ip_addrs = [tb_config_obj.get_interface_ipv4_addr(hu, intf) for intf in interfaces]

        min_pkt_size = 46
        max_pkt_size = MAX_MTU
        pkt_count = 2
        interval = 0.01

        def get_icmp_payload_size(pkt_size):
            return pkt_size - 20 - 8  # IP header 20B, ICMP header 8B

        for intf, ip_addr in zip(interfaces, ip_addrs):
            cmd = 'for i in {%s..%s}; do sudo ping -c %s -i %s -s $i %s; done' % (
                get_icmp_payload_size(min_pkt_size), get_icmp_payload_size(max_pkt_size), pkt_count, interval, ip_addr)
            output = linux_obj.command(cmd, timeout=3000)
            fun_test.test_assert(
                re.search(r'[1-9]+% packet loss', output) is None and re.search(r'cannot', output) is None,
                'NU ping HU interfaces {} with packet sizes {}-{}B'.format(intf, min_pkt_size, max_pkt_size))


class FunethTestScpBase(FunTestCase):

    def _setup(self, nu_or_hu, pf_or_vf=None):
        """Create a file and/or start sshd for scp.

        :param nu_or_hu: host to execute scp cmd, 'nu' or 'hu', i.e. scp source host
        :param pf_or_vf: if scp destination is 'hu', whether to use 'pf' or 'vf' interface IP
        """

        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict[nu_or_hu]
        self.file_name = '/tmp/{}file'.format(nu_or_hu)

        # Create a file
        if TB == 'SN2':
            file_size = '2m'
        else:
            file_size = '2g'
        linux_obj.command('xfs_mkfile {} {}'.format(file_size, self.file_name))
        fun_test.test_assert(linux_obj.check_file_directory_exists(self.file_name),
                             'Create file {} in {}'.format(self.file_name, linux_obj.host_ip))

        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'

        # Start sshd in namespace if needed
        if nu_or_hu == nu:
            tb_config_obj = funeth_obj.tb_config_obj
            if pf_or_vf == 'pf':
                ns = tb_config_obj.get_hu_pf_namespace(hu)
            elif pf_or_vf == 'vf':
                ns = tb_config_obj.get_hu_vf_namespace(hu)

            if ns:
                linux_obj = funeth_obj.linux_obj_dict[hu]
                linux_obj.command('sudo ip netns exec {} /usr/sbin/sshd &'.format(ns))

    def cleanup(self):
        pass

    def _run(self, nu_or_hu, pf_or_vf=None):
        """Run scp test.

        :param nu_or_hu: host to execute scp cmd, 'nu' or 'hu', i.e. scp source host
        :param pf_or_vf: if scp destination is 'hu', whether to use 'pf' or 'vf' interface IP
        """
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict[nu_or_hu]
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'

        if nu_or_hu == nu:
            if pf_or_vf == 'pf':
                ip_addr = tb_config_obj.get_interface_ipv4_addr(hu, tb_config_obj.get_hu_pf_interface(hu))
            elif pf_or_vf == 'vf':
                ip_addr = tb_config_obj.get_interface_ipv4_addr(hu, tb_config_obj.get_hu_vf_interface(hu))
            username = tb_config_obj.get_username(hu)
            password = tb_config_obj.get_password(hu)
            desc = 'Scp a file from NU to HU host via {}.'.format(pf_or_vf.upper())
        elif nu_or_hu == hu:
            ip_addr = tb_config_obj.get_interface_ipv4_addr(nu, tb_config_obj.get_a_nu_interface())
            username = tb_config_obj.get_username(hu)
            password = tb_config_obj.get_password(hu)
            desc = 'Scp a file from HU to NU host.'

        collect_stats()
        result = linux_obj.scp(source_file_path=self.file_name,
                                           target_ip=ip_addr,
                                           target_file_path='{}{}'.format(
                                               self.file_name, '' if not pf_or_vf else pf_or_vf),
                                           target_username=username,
                                           target_password=password,
                                           timeout=300),
        collect_stats()
        fun_test.test_assert(result, desc)


class FunethTestScpNU2HUPF(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Scp a file from NU to HU host via PF.",
                              steps="""
        1. Scp a file from NU to HU host via PF interface.
        """)

    def setup(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        FunethTestScpBase._setup(self, nu, 'pf')

    def run(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        FunethTestScpBase._run(self, nu, 'pf')


class FunethTestScpNU2HUVF(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Scp a file from NU to HU host via VF.",
                              steps="""
        1. Scp a file from NU to HU host via VF interface.
        """)

    def setup(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        FunethTestScpBase._setup(self, nu, 'vf')

    def run(self):
        FunethTestScpBase._run(self, nu, 'vf')


class FunethTestScpHU2NU(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Scp a file from HU to NU host.",
                              steps="""
        1. Scp a file from HU to NU host.
        """)

    def setup(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        FunethTestScpBase._setup(self, hu)

    def run(self):
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        FunethTestScpBase._run(self, hu)


class FunethTestInterfaceFlapBase(FunTestCase):

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, pf_or_vf):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'

        linux_obj = funeth_obj.linux_obj_dict[hu]
        if pf_or_vf == 'pf':
            namespace = tb_config_obj.get_hu_pf_namespace(hu)
            interface = tb_config_obj.get_hu_pf_interface(hu)
        elif pf_or_vf == 'vf':
            namespace = tb_config_obj.get_hu_vf_namespace(hu)
            interface = tb_config_obj.get_hu_vf_interface(hu)
        ns = None if namespace == 'default' else namespace

        # ifconfig down
        fun_test.test_assert(linux_obj.ifconfig_up_down(interface, action='down', ns=ns),
                             'ifconfig {} down'.format(interface))
        verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[interface])

        # ifconfig up
        fun_test.test_assert(linux_obj.ifconfig_up_down(interface, action='up', ns=ns),
                             'ifconfig {} up'.format(interface))
        # Need to re-configure route/arp
        fun_test.test_assert(funeth_obj.configure_namespace_ipv4_routes(hu, ns=namespace),
                             'Configure HU host IPv4 routes.')
        verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[])


class FunethTestInterfaceFlapPF(FunethTestInterfaceFlapBase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Shut and no shut HU host PF interface.",
                              steps="""
        1. In HU host, shut down PF interface
        2. From NU host, ping all other PF/VF interfaces
        """)

    def run(self):
        FunethTestInterfaceFlapBase._run(self, 'pf')


class FunethTestInterfaceFlapVF(FunethTestInterfaceFlapBase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Shut and no shut HU host VF interface.",
                              steps="""
        1. In HU host, shut down VF interface
        2. From NU host, ping all other PF/VF interfaces
        """)

    def run(self):
        FunethTestInterfaceFlapBase._run(self, 'vf')


class FunethTestUnloadDriver(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Unload funeth driver and reload it.",
                              steps="""
        1. Unload funeth driver.
        2. Load funeth driver and configure interfaces/routes/arps.
        3. From NU host, Ping HU host PF/VF interfaces.
        """)

    def setup(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']

        # Unload driver
        fun_test.test_assert(funeth_obj.unload(), 'Unload funeth driver.')

        # Load driver and configure interfaces/routes/arps
        setup_hu_host(funeth_obj, update_driver=False)

    def cleanup(self):
        pass

    def run(self):
        verify_nu_hu_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'])


class FunethTestReboot(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Reboot HU host.",
                              steps="""
        1. Reboot HU host.
        2. Load funeth driver and configure interfaces/routes/arps.
        3. From NU host, Ping HU host PF/VF interfaces.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        tb_config_obj = funeth_obj.tb_config_obj
        if fun_test.shared_variables["test_bed_type"] == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        linux_obj = funeth_obj.linux_obj_dict[hu]
        hostname = tb_config_obj.get_hostname(hu)

        fun_test.test_assert(linux_obj.reboot(timeout=60, retries=5), 'Reboot HU host {}'.format(hostname))
        fun_test.test_assert(linux_obj.is_host_up(), 'HU host {} is up'.format(hostname))
        setup_hu_host(funeth_obj, update_driver=False)
        verify_nu_hu_datapath(funeth_obj)


if __name__ == "__main__":
    ts = FunethSanity()
    for tc in (
            FunethTestNUPingHU,
            FunethTestPacketSweep,
            FunethTestScpNU2HUPF,
            FunethTestScpNU2HUVF,
            FunethTestScpHU2NU,
            FunethTestInterfaceFlapPF,
            FunethTestInterfaceFlapVF,
            FunethTestUnloadDriver,  # TODO: uncomment after EM-914 is fixed
            FunethTestReboot,
    ):
        ts.add_test_case(tc())
    ts.run()
