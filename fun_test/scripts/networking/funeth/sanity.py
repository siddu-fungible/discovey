from lib.system.fun_test import *
from fun_settings import DATA_STORE_DIR
from fun_settings import SCRIPTS_DIR
from lib.host.linux import Linux
from lib.topology.topology_helper import TopologyHelper
from lib.host import netperf_manager
from lib.host.network_controller import NetworkController
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.utilities.funcp_config import FunControlPlaneBringup
from scripts.networking.funeth.funeth import Funeth, CPU_LIST_HOST, CPU_LIST_VM
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import perf_utils


import re
import struct


fun_test.enable_profiling()


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
    DPC_PROXY_IP = 'fs11-come'
    DPC_PROXY_PORT = 42220
    DPC_PROXY_IP2 = 'fs11-come'
    DPC_PROXY_PORT2 = 42221
    TB = ''.join(fun_test.get_job_environment_variable('test_bed_type').split('-')).upper()

try:
    inputs = fun_test.get_job_inputs()
    if inputs:
        enable_tso = (inputs.get('lso', 1) == 1)  # Enable TSO or not
        control_plane = (inputs.get('control_plane', 0) == 1)  # Use control plane or not
        update_funcp = (inputs.get('update_funcp', 1) == 1)  # Update FunControlPlane binary or not
        update_driver = (inputs.get('update_driver', 1) == 1)  # Update driver or not
        hu_host_vm = (inputs.get('hu_host_vm', 0) == 1)  # HU host runs VMs or not
        configure_overlay = (inputs.get('configure_overlay', 0) == 1)  # Enable overlay config or not
        cleanup = (inputs.get('cleanup', 1) == 1)  # Clean up funeth and control plane or not
        ol_offload = (inputs.get('ol_offload', 0) == 1)  # Enable overlay TSO/checksum offload or not
        nu_all_clusters = (inputs.get('nu_all_clusters', 0) == 1)  # Enable NU to use all the clusters or not
        bootup_funos = (inputs.get('bootup_funos', 1) == 1)  # Boot up FunOS or not
        threading = (inputs.get('threading', 1) == 1)  # Use threading in multi task or not
        fundrv_branch = inputs.get('fundrv_branch', None)
        fundrv_commit = inputs.get('fundrv_commit', None)
        funsdk_branch = inputs.get('funsdk_branch', None)
        funsdk_commit = inputs.get('funsdk_commit', None)
    else:
        enable_tso = True  # default True
        control_plane = False  # default False
        update_funcp = True  # default True
        update_driver = True  # default True
        hu_host_vm = False  # default False
        configure_overlay = False  # default False
        ol_offload = False  # default False
        nu_all_clusters = False  # default False
        bootup_funos = True  # default True
        threading = True   # default True
        cleanup = True  # default True
        fundrv_branch = None
        fundrv_commit = None
        funsdk_branch = None
        funsdk_commit = None
except:
    enable_tso = True
    control_plane = False
    update_funcp = True
    update_driver = True
    hu_host_vm = False
    configure_overlay = False
    ol_offload = False
    nu_all_clusters = False
    bootup_funos = True
    threading = True
    cleanup = True

csi_perf_enabled = fun_test.get_job_environment_variable("csi_perf")
csi_cache_miss_enabled = fun_test.get_job_environment_variable("csi_cache_miss")
perf_listener_host_name = "poc-server-06"
perf_listener_ip = "20.1.1.1"

NUM_VFs = 4
NUM_QUEUES_TX = 8
NUM_QUEUES_RX = 8
MAX_MTU = 1500  # TODO: change to 9000, note, need ifconfig down/up for it to be effective until SWOS-6025 is fixed

supported_testbed_types = ('fs-11', 'fs-48', )


def setup_nu_host(funeth_obj):
    #if TB in ('FS7', 'FS11'):
        #for nu in funeth_obj.nu_hosts:
        #    linux_obj = funeth_obj.linux_obj_dict[nu]
        #    fun_test.test_assert(linux_obj.reboot(non_blocking=True), 'NU host {} reboot'.format(linux_obj.host_ip))
        #fun_test.sleep("Sleeping for the host to come up from reboot", seconds=30)
    for nu in funeth_obj.nu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[nu]
        #if TB in ('FS7', 'FS11'):
            #fun_test.test_assert(linux_obj.reboot(timeout=60, retries=5), 'Reboot NU host')
        fun_test.test_assert(linux_obj.is_host_up(), 'NU host {} is up'.format(linux_obj.host_ip))
        linux_obj.command('sudo sysctl net.ipv6.conf.all.disable_ipv6=0')
        fun_test.test_assert(funeth_obj.configure_interfaces(nu), 'Configure NU host {} interface'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(nu, configure_gw_arp=(not control_plane)),
                             'Configure NU host {} IPv4 routes'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv6_routes(nu),
                             'Configure NU host {} IPv6 routes'.format(linux_obj.host_ip))
        # TODO: temp workaround
        if linux_obj.host_ip == 'poc-server-06':
            if enable_tso:
                linux_obj.sudo_command('sudo pkill dockerd; sudo ethtool -K fpg0 lro on; sudo ethtool -k fpg0')
            else:
                linux_obj.sudo_command('sudo pkill dockerd; sudo ethtool -K fpg0 lro off; sudo ethtool -k fpg0')


def setup_hu_host(funeth_obj, update_driver=True, is_vm=False, tx_offload=True):
    funsdk_commit = funsdk_bld = driver_commit = driver_bld = None
    if is_vm:
        lspci_result = funeth_obj.lspci(check_pcie_width=False)
    else:
        lspci_result = funeth_obj.lspci(check_pcie_width=True)
    fun_test.test_assert(lspci_result, 'Fungible Ethernet controller is seen.')
    if update_driver:
        funeth_obj.setup_workspace()
        update_src_result = funeth_obj.update_src(parallel=True)
        if update_src_result:
            funsdk_commit, funsdk_bld, driver_commit, driver_bld = update_src_result
        fun_test.test_assert(update_src_result, 'Update funeth driver source code.')
    fun_test.test_assert(funeth_obj.build(parallel=True), 'Build funeth driver.')
    if is_vm:
        load_result = funeth_obj.load(sriov=0)
    else:
        load_result = funeth_obj.load(sriov=NUM_VFs)
    fun_test.test_assert(load_result, 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]
        linux_obj.command('sudo sysctl net.ipv6.conf.all.disable_ipv6=0')
        if enable_tso:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=False),
                                 'Enable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))
        else:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=True),
                                 'Disable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))

        # TODO: no need after LSO/checksum offload is enabled for overlay
        if not tx_offload:
            fun_test.test_assert(funeth_obj.enable_tx_offload(hu, disable=True),
                                 'Disable HU host {} funeth interfaces Tx offload.'.format(linux_obj.host_ip))

        if is_vm:
            cpu_list = CPU_LIST_VM
        else:
            cpu_list = CPU_LIST_HOST
        fun_test.test_assert(
            funeth_obj.enable_multi_queues(hu, num_queues_tx=NUM_QUEUES_TX, num_queues_rx=NUM_QUEUES_RX,
                                           cpu_list=cpu_list),
            'Enable HU host {} funeth interfaces {} Tx queues, {} Rx queues.'.format(linux_obj.host_ip, NUM_QUEUES_TX,
                                                                                     NUM_QUEUES_RX))
        fun_test.test_assert(
            funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(hu, configure_gw_arp=(not control_plane)),
                             'Configure HU host {} IPv4 routes.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv6_routes(hu),
                             'Configure HU host {} IPv6 routes.'.format(linux_obj.host_ip))
        fun_test.test_assert(
            funeth_obj.configure_arps(hu), 'Configure HU host {} ARP entries.'.format(linux_obj.host_ip))
        #fun_test.test_assert(funeth_obj.loopback_test(packet_count=80),
        #                    'HU PF and VF interface loopback ping test via NU')

    return funsdk_commit, funsdk_bld, driver_commit, driver_bld


def setup_funcp(test_bed_type, update_funcp=True):
    funcp_obj = FunControlPlaneBringup(fs_name=test_bed_type)
    funcp_obj.bringup_funcp(prepare_docker=update_funcp)
    # TODO: Make it setup independent
    funcp_obj.assign_mpg_ips(static=True, f1_1_mpg='10.1.20.241', f1_0_mpg='10.1.20.242',
                             f1_0_mpg_netmask="255.255.252.0",
                             f1_1_mpg_netmask="255.255.252.0"
                             )
    abstract_json_file_f1_0 = '{}/networking/tb_configs/FS11_F1_0.json'.format(SCRIPTS_DIR)
    abstract_json_file_f1_1 = '{}/networking/tb_configs/FS11_F1_1.json'.format(SCRIPTS_DIR)
    funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file_f1_0,
                                    abstract_config_f1_1=abstract_json_file_f1_1)
    #fun_test.sleep("Sleeping for a while waiting for control plane to converge", seconds=10)
    # TODO: sanity check of control plane


class FunCPSetup:
    def __init__(self, test_bed_type, update_funcp=True):
        self.funcp_obj = FunControlPlaneBringup(fs_name=test_bed_type)
        self.update_funcp = update_funcp

    def bringup(self, fs):
        self.funcp_obj.bringup_funcp(prepare_docker=self.update_funcp)
        # TODO: Make it setup independent
        self.funcp_obj.assign_mpg_ips(static=True, f1_1_mpg='10.1.20.241', f1_0_mpg='10.1.20.242',
                                      f1_0_mpg_netmask="255.255.252.0",
                                      f1_1_mpg_netmask="255.255.252.0"
                                      )
        abstract_json_file_f1_0 = '{}/networking/tb_configs/FS11_F1_0.json'.format(SCRIPTS_DIR)
        abstract_json_file_f1_1 = '{}/networking/tb_configs/FS11_F1_1.json'.format(SCRIPTS_DIR)
        self.funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file_f1_0,
                                             abstract_config_f1_1=abstract_json_file_f1_1)


def setup_funcp_on_fs(test_bed_type):

    testbed_info = fun_test.parse_file_to_json(SCRIPTS_DIR +
                                               '/networking/funcp/abstract_config/abstract_config_key.json')
    funcp_obj = FunControlPlaneBringup(fs_name=test_bed_type)
    funcp_obj.bringup_funcp(prepare_docker=True)
    funcp_obj.assign_mpg_ips(static=True, f1_1_mpg=str(testbed_info['fs'][test_bed_type]['mpg1']),
                             f1_0_mpg=str(testbed_info['fs'][test_bed_type]['mpg0']))

    abstract_json_file_f1_0 = '%s/networking/tb_configs/%s_F1_0.json' % (SCRIPTS_DIR, TB)
    abstract_json_file_f1_1 = '%s/networking/tb_configs/%s_F1_1.json' % (SCRIPTS_DIR, TB)
    funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file_f1_0,
                                    abstract_config_f1_1=abstract_json_file_f1_1)
    fun_test.sleep("Sleeping for a while waiting for control plane to converge", seconds=10)
    # TODO: sanity check of control plane


def start_vm(funeth_obj_hosts, funeth_obj_vms):
    for vm in funeth_obj_vms.hu_hosts:
        vm_host = funeth_obj_vms.tb_config_obj.get_vm_host(vm)
        vm_name = funeth_obj_vms.tb_config_obj.get_hostname(vm)  # VM name and VM's hostname are kept same
        pci_info = funeth_obj_vms.tb_config_obj.get_vm_host_pci_info(vm)
        for hu in funeth_obj_hosts.hu_hosts:
            if funeth_obj_hosts.tb_config_obj.get_hostname(hu) == vm_host:
                linux_obj = funeth_obj_hosts.linux_obj_dict[hu]
                cmds = ['virsh nodedev-dettach {}'.format(pci_info), 'virsh start {}'.format(vm_name)]
                for cmd in cmds:
                    linux_obj.sudo_command(cmd)


def dpcsh_configure_overlay(network_controller_obj_f1_0, network_controller_obj_f1_1):

    # TODO: Define overlay args in config file
    overlay_config_dict = {
        network_controller_obj_f1_0: [
            {'lport_num': 265, 'vtep': '53.1.1.1', 'vnids': [20100, ], 'flows': ['50.1.1.8', ], 'vif_table_mac_entries': ['00:de:ad:be:ef:31', ]},
            {'lport_num': 393, 'vtep': '53.1.1.4', 'vnids': [20100, ], 'flows': ['50.1.1.9', ], 'vif_table_mac_entries': ['00:de:ad:be:ef:41', ]},
        ],
        network_controller_obj_f1_1: [
            {'lport_num': 265, 'vtep': '54.1.1.1', 'vnids': [20100, ], 'flows': ['50.1.2.8', ], 'vif_table_mac_entries': ['00:de:ad:be:ef:51', ]},
            {'lport_num': 521, 'vtep': '54.1.1.4', 'vnids': [20100, ], 'flows': ['50.1.2.9', ], 'vif_table_mac_entries': ['00:de:ad:be:ef:61', ]},
        ]
    }

    # num_flows, 512k
    for nc_obj in overlay_config_dict:
        nc_obj.overlay_num_flows(512 * 1024)

    nc_obj_src, nc_obj_dst = network_controller_obj_f1_0, network_controller_obj_f1_1
    for src, dst in zip(overlay_config_dict[nc_obj_src], overlay_config_dict[nc_obj_dst]):
        for nc_obj in (nc_obj_src, nc_obj_dst):
            if nc_obj == nc_obj_src:
                lport_num = src['lport_num']
                vnids = src['vnids']
                src_vtep = src['vtep']
                dst_vtep = dst['vtep']
                src_flows = src['flows']
                dst_flows = dst['flows']
                vif_table_mac_entries = src['vif_table_mac_entries']
            else:
                lport_num = dst['lport_num']
                vnids = dst['vnids']
                src_vtep = dst['vtep']
                dst_vtep = src['vtep']
                src_flows = dst['flows']
                dst_flows = src['flows']
                vif_table_mac_entries = dst['vif_table_mac_entries']

            # vif
            nc_obj.overlay_vif_add(lport_num=lport_num)
            for vnid in vnids:
                # nh
                #nc_obj.overlay_nh_add(nh_type='vxlan_encap', src_vtep=src_vtep, dst_vtep=dst_vtep, vnid=vnid)
                #nc_obj.overlay_nh_add(nh_type='vxlan_decap', src_vtep=dst_vtep, dst_vtep=src_vtep, vnid=vnid)
                for nh_type in ('vxlan_encap', 'vxlan_decap'):
                    nc_obj.overlay_nh_add(nh_type=nh_type, src_vtep=src_vtep, dst_vtep=dst_vtep, vnid=vnid)
                # flows
                #for flow_type, nh_index in zip(('vxlan_encap', 'vxlan_decap'), (0, 1)):
                #    for sip, dip in zip(src_flows, dst_flows):
                #        if flow_type == 'vxlan_encap':
                #            flow_sip, flow_dip = sip, dip
                #            if nc_obj == nc_obj_src:
                #                flow_sport, flow_dport = 0, netperf_manager.NETSERVER_PORT
                #            elif nc_obj == nc_obj_dst:
                #                flow_sport, flow_dport = netperf_manager.NETSERVER_PORT, 0
                #        elif flow_type == 'vxlan_decap':
                #            flow_sip, flow_dip = dip, sip
                #            if nc_obj == nc_obj_src:
                #                flow_sport, flow_dport = netperf_manager.NETSERVER_PORT, 0
                #            elif nc_obj == nc_obj_dst:
                #                flow_sport, flow_dport = 0, netperf_manager.NETSERVER_PORT
                #        nc_obj.overlay_flow_add(flow_type=flow_type,
                #                                nh_index=nh_index,
                #                                vif=lport_num,
                #                                flow_sip=flow_sip,
                #                                flow_dip=flow_dip,
                #                                flow_sport=flow_sport,
                #                                flow_dport=flow_dport,
                #                                flow_proto=6
                #                                )
                for i in CPU_LIST_VM[::-1] + [(CPU_LIST_VM)[::-1][-1]-1]:  # last one - 1 is for TCP_RR
                    for j in (netperf_manager.NETSERVER_FIXED_PORT_CONTROL_BASE,
                              netperf_manager.NETSERVER_FIXED_PORT_DATA_BASE):
                        for flow_type, nh_index in zip(('vxlan_encap', 'vxlan_decap'), (0, 1)):
                            for sip, dip in zip(src_flows, dst_flows):
                                if flow_type == 'vxlan_encap':
                                    flow_sip, flow_dip = sip, dip
                                else:
                                    flow_sip, flow_dip = dip, sip
                                # flows
                                nc_obj.overlay_flow_add(
                                    flow_type=flow_type,
                                    nh_index=nh_index,
                                    vif=lport_num,
                                    flow_sip=flow_sip,
                                    flow_dip=flow_dip,
                                    flow_sport=i+j,
                                    flow_dport=i+j,
                                    flow_proto=6
                                )
                # vif_table
                for mac_addr in vif_table_mac_entries:
                    nc_obj.overlay_vif_table_add_mac_entry(vnid=vnid, mac_addr=mac_addr, egress_vif=lport_num)
            # vtep
            nc_obj.overlay_vtep_add(ipaddr=src_vtep)


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
        if test_bed_type not in supported_testbed_types:
            fun_test.test_assert(False, 'This test only runs in {}.'.format(','.join(supported_testbed_types)))
        else:
            #TB = 'FS11'
            TB = ''.join(test_bed_type.split('-')).upper()
            if control_plane:
                if test_bed_type == 'fs-11':
                    f1_0_boot_args = "app=load_mods cc_huid=3 sku=SKU_FS1600_0 retimer=0,1 --all_100g --dpc-uart --dpc-server"
                    f1_1_boot_args = "app=load_mods cc_huid=2 sku=SKU_FS1600_1 retimer=0,1 --all_100g --dpc-uart --dpc-server"
                if test_bed_type == 'fs-48':
                    f1_0_boot_args = "app=load_mods cc_huid=3 sku=SKU_FS1600_0 retimer=0,1,2 --all_100g --dpc-uart --dpc-server"
                    f1_1_boot_args = "app=load_mods cc_huid=2 sku=SKU_FS1600_1 retimer=0 --all_100g --dpc-uart --dpc-server"
                if csi_perf_enabled:
                    f1_0_boot_args += " --perf"
                    f1_0_boot_args += " csi-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(perf_listener_ip)
                elif csi_cache_miss_enabled:
                    f1_0_boot_args += " --csi-cache-miss"
                    f1_0_boot_args += " csi	-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(perf_listener_ip)
                if nu_all_clusters:
                    f1_0_boot_args += ' override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]}'
                    f1_1_boot_args += ' override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]}'
                funcp_setup_obj = FunCPSetup(test_bed_type=test_bed_type, update_funcp=update_funcp)
                topology_helper = TopologyHelper()
                topology_helper.set_dut_parameters(dut_index=0,
                                                   f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                                  1: {"boot_args": f1_1_boot_args}},
                                                   fun_cp_callback=funcp_setup_obj.bringup)
            else:
                boot_args = "app=load_mods retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g"
                if csi_perf_enabled:
                    boot_args += " --perf"
                    boot_args += " csi-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(
                        perf_listener_ip)
                elif csi_cache_miss_enabled:
                    boot_args += " --csi-cache-miss"
                    boot_args += " csi-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(
                        perf_listener_ip)
                if nu_all_clusters:
                    boot_args += ' override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]}'
                topology_helper = TopologyHelper()
                topology_helper.set_dut_parameters(dut_index=0,
                                                   custom_boot_args=boot_args)

            if bootup_funos:
                topology = topology_helper.deploy()
                fun_test.shared_variables["topology"] = topology
                fun_test.test_assert(topology, "Topology deployed")
                fs = topology.get_dut_instance(index=0)

                come = fs.get_come()
                global DPC_PROXY_IP
                global DPC_PROXY_PORT
                global DPC_PROXY_PORT2
                DPC_PROXY_IP = come.host_ip
                DPC_PROXY_PORT = come.get_dpc_port(0)
                DPC_PROXY_PORT2 = come.get_dpc_port(1)
                self.come_linux_obj = Linux(host_ip=come.host_ip,
                                            ssh_username=come.ssh_username,
                                            ssh_password=come.ssh_password)
                fun_test.shared_variables["come_linux_obj"] = self.come_linux_obj

        network_controller_obj_f1_0 = NetworkController(dpc_server_ip=DPC_PROXY_IP, dpc_server_port=DPC_PROXY_PORT,
                                                        verbose=True)
        network_controller_obj_f1_1 = NetworkController(dpc_server_ip=DPC_PROXY_IP, dpc_server_port=DPC_PROXY_PORT2,
                                                        verbose=True)
        fun_test.shared_variables['network_controller_obj'] = network_controller_obj_f1_0

        # TODO: make it work for other setup
        #if test_bed_type == 'fs-11' and control_plane:
        #    setup_funcp(test_bed_type, update_funcp=update_funcp)
        if test_bed_type != 'fs-11' and control_plane:
            setup_funcp_on_fs(test_bed_type, update_funcp=update_funcp)
        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = Funeth(tb_config_obj,
                            fundrv_branch=fundrv_branch,
                            funsdk_branch=funsdk_branch,
                            fundrv_commit=fundrv_commit,
                            funsdk_commit=funsdk_commit)
        self.funeth_obj = funeth_obj
        fun_test.shared_variables['funeth_obj'] = funeth_obj

        # perf
        if csi_perf_enabled or csi_cache_miss_enabled:
            p = CsiPerfTemplate(perf_collector_host_name=perf_listener_host_name, listener_ip=perf_listener_ip, fs=fs)
            p.prepare(f1_index=0)
            self.csi_perf_obj = p

        # threading
        self.threading = threading

        # HU host
        self.funsdk_commit, self.funsdk_bld, self.driver_commit, self.driver_bld = setup_hu_host(
            funeth_obj, update_driver=update_driver)

        # NU host
        setup_nu_host(funeth_obj)

        # HU host VMs
        if hu_host_vm:
            tb_config_obj_ul_vm = tb_configs.TBConfigs(tb_configs.get_tb_name_vm(TB, 'ul'))
            tb_config_obj_ol_vm = tb_configs.TBConfigs(tb_configs.get_tb_name_vm(TB, 'ol'))
            funeth_obj_ul_vm = Funeth(tb_config_obj_ul_vm,
                                      fundrv_branch=fundrv_branch,
                                      funsdk_branch=funsdk_branch,
                                      fundrv_commit=fundrv_commit,
                                      funsdk_commit=funsdk_commit)
            funeth_obj_ol_vm = Funeth(tb_config_obj_ol_vm,
                                      fundrv_branch=fundrv_branch,
                                      funsdk_branch=funsdk_branch,
                                      fundrv_commit=fundrv_commit,
                                      funsdk_commit=funsdk_commit)
            self.funeth_obj_ul_vm = funeth_obj_ul_vm
            self.funeth_obj_ol_vm = funeth_obj_ol_vm
            fun_test.shared_variables['funeth_obj_ul_vm'] = funeth_obj_ul_vm
            fun_test.shared_variables['funeth_obj_ol_vm'] = funeth_obj_ol_vm

            # start VMs
            start_vm(funeth_obj_hosts=funeth_obj, funeth_obj_vms=funeth_obj_ul_vm)
            start_vm(funeth_obj_hosts=funeth_obj, funeth_obj_vms=funeth_obj_ol_vm)
            fun_test.sleep("Sleeping for a while waiting for VMs to come up", seconds=10)

            setup_hu_host(funeth_obj=funeth_obj_ul_vm, update_driver=update_driver, is_vm=True)
            setup_hu_host(funeth_obj=funeth_obj_ol_vm, update_driver=update_driver, is_vm=True, tx_offload=ol_offload)

            # Configure overlay
            if configure_overlay:
                dpcsh_configure_overlay(network_controller_obj_f1_0, network_controller_obj_f1_1)
                network_controller_obj_f1_0.disconnect()
                network_controller_obj_f1_1.disconnect()

        if test_bed_type == 'fs-11':
            nu = 'nu2'
            hu = 'hu2'
        else:
            nu = 'nu'
            hu = 'hu'
        fun_test.shared_variables['sanity_nu'] = nu
        fun_test.shared_variables['sanity_hu'] = hu

    def cleanup(self):
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fun_test.shared_variables["fs"].cleanup()
        elif fun_test.get_job_environment_variable('test_bed_type') == 'fs-11':
            topology = fun_test.shared_variables["topology"]
            topology.cleanup()
            try:
                if hu_host_vm:
                    funeth_obj_descs = ['funeth_obj_ul_vm', 'funeth_obj_ol_vm', 'funeth_obj']
                else:
                    funeth_obj_descs = ['funeth_obj', ]
                for funeth_obj_desc in funeth_obj_descs:
                    funeth_obj = fun_test.shared_variables[funeth_obj_desc]
                    funeth_obj.cleanup_workspace()
                    fun_test.log("Collect syslog from HU hosts")
                    funeth_obj.collect_syslog()
                    fun_test.log("Collect dmesg from HU hosts")
                    funeth_obj.collect_dmesg()
                    if cleanup:
                        fun_test.log("Unload funeth driver")
                        funeth_obj.unload()

                # Close ssh sessions
                for funeth_obj_desc in funeth_obj_descs:
                    funeth_obj = fun_test.shared_variables[funeth_obj_desc]
                    for linux_obj in funeth_obj.linux_obj_dict.values():
                        linux_obj.disconnect()
            except:
                if cleanup:
                    hu_hosts = topology.get_host_instances_on_ssd_interfaces(dut_index=0)
                    for host_ip, host_info in hu_hosts.iteritems():
                        host_info["host_obj"].ensure_host_is_up(max_wait_time=2, power_cycle=True)

            if control_plane:
                perf_utils.collect_funcp_logs(self.come_linux_obj)
                if cleanup:
                    try:
                        self.come_linux_obj.sudo_command('rmmod funeth')
                        self.come_linux_obj.sudo_command('docker kill F1-0 F1-1')
                        self.come_linux_obj.sudo_command('rm -fr /tmp/*')
                    except:
                        self.come_linux_obj.ensure_host_is_up(max_wait_time=0, power_cycle=True)


def collect_stats(when='before'):
    network_controller_objs = [fun_test.shared_variables['network_controller_obj'], ]
    fpg_interfaces = (4, )
    fpg_intf_dict = {'F1_0': (4, )}
    version = fun_test.get_version()
    fun_test.log('Collect stats via DPC and save to file {} test'.format(when))
    fun_test.log_module_filter("random_module")
    try:
        perf_utils.collect_dpc_stats(network_controller_objs, fpg_interfaces, fpg_intf_dict, version, when=when)
        fun_test.log_module_filter_disable()
    except:
        fun_test.log_module_filter_disable()


def verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[], nu='nu', hu='hu'):
    linux_obj = funeth_obj.linux_obj_dict[nu]
    tb_config_obj = funeth_obj.tb_config_obj

    interfaces = [i for i in tb_config_obj.get_all_interfaces(hu) if i not in interfaces_excludes]
    ip_addrs = [tb_config_obj.get_interface_ipv4_addr(hu, intf) for intf in interfaces]

    # Collect dpc stats before and after the test
    collect_stats(when='before')

    result = True
    for intf, ip_addr in zip(interfaces, ip_addrs):
        result &= linux_obj.ping(ip_addr, count=packet_count, max_percentage_loss=0, interval=0.1,
                                 size=packet_size-20-8,  # IP header 20B, ICMP header 8B
                                 sudo=True)
    collect_stats(when='after')

    fun_test.shared_variables['nu_hu_pingable'] = result
    fun_test.test_assert(
        result,
        'NU ping HU interfaces {} with {} packets and packet size {}B'.format(intf, packet_count, packet_size))


def check_nu_hu_pingable():
    if not fun_test.shared_variables['nu_hu_pingable']:
        fun_test.test_assert(False, 'NU ping HU unsuccessful, stop further testing')


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
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
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
        check_nu_hu_pingable()
        funeth_obj = fun_test.shared_variables['funeth_obj']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']

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
            fun_test.test_assert(linux_obj.set_mtu(interface, MAX_MTU, ns=namespace),
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
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
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

        # Collect dpc stats before and after the test
        collect_stats(when='before')

        timeout = 600
        result = True
        for intf, ip_addr in zip(interfaces, ip_addrs):
            script_file = '/tmp/packet_sweep.sh'
            linux_obj.command('rm {0}; touch {0}'.format(script_file))
            cmd_str_list = ['{',
                            '    sleep %s' % timeout,
                            '    kill \$\$',
                            '} &',
                            'for i in {%s..%s}; do sudo ping -c %s -i %s -s \$i -M do %s; done' % (
                                get_icmp_payload_size(min_pkt_size), get_icmp_payload_size(max_pkt_size), pkt_count,
                                interval, ip_addr),
                            ]
            for cmd_str in cmd_str_list:
                linux_obj.command('echo "{}" >> {}'.format(cmd_str, script_file))
            linux_obj.command('cat {}'.format(script_file))
            linux_obj.command('chmod +x {}'.format(script_file))
            fun_test.log('NU ping HU interfaces {} with packet sizes {}-{}B'.format(intf, min_pkt_size, max_pkt_size))
            output = linux_obj.command('bash {}'.format(script_file), timeout=timeout+2)
            #result &= re.search(r'[1-9]+% packet loss', output) is None and re.search(r'cannot', output) is None
            result &= len(re.findall(r' (0% packet loss)', output)) == (max_pkt_size - min_pkt_size + 1)

        collect_stats(when='after')
        fun_test.test_assert(result, 'Packet sweep test')


class FunethTestScpBase(FunTestCase):

    def _setup(self, nu_or_hu, pf_or_vf=None):
        """Create a file and/or start sshd for scp.

        :param nu_or_hu: host to execute scp cmd, 'nu' or 'hu', i.e. scp source host
        :param pf_or_vf: if scp destination is 'hu', whether to use 'pf' or 'vf' interface IP
        """
        check_nu_hu_pingable()
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict[nu_or_hu]
        self.file_name = '/tmp/{}file'.format(nu_or_hu)

        # Create a file
        #if TB == 'SN2':
        #    file_size = '2m'
        #else:
        #    file_size = '2g'
        #linux_obj.command('xfs_mkfile {} {}'.format(file_size, self.file_name))

        # Create file with pattern of sequential 32-bit
        if TB == 'SN2':
            file_size = 2000000  # 2MB
        else:
            file_size = 200000000  # 200MB

        # Create file in regression server
        lista = list(range(0, file_size/4))
        packer = struct.Struct('I ' * (file_size/4))
        content = packer.pack(*lista)
        tmp_filename = '{}/networking/funeth_sanity_scp_test_file'.format(DATA_STORE_DIR)
        fun_test.log("Write {} 32-bit sequential patterns to file {}".format(file_size/4, tmp_filename))
        with open(tmp_filename, 'w') as f:
            f.write(content)

        # Scp file to test server
        fun_test.scp(source_file_path=tmp_filename,
                     target_ip=linux_obj.host_ip,
                     target_username=linux_obj.ssh_username,
                     target_password=linux_obj.ssh_password,
                     target_file_path=self.file_name)
        linux_obj.command('ls -l {}'.format(self.file_name))
        fun_test.test_assert(linux_obj.check_file_directory_exists(self.file_name),
                             'Create file {} in {}'.format(self.file_name, linux_obj.host_ip))

        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']

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

        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']

        if nu_or_hu == nu:
            if pf_or_vf == 'pf':
                ip_addr = tb_config_obj.get_interface_ipv4_addr(hu, tb_config_obj.get_hu_pf_interface(hu))
            elif pf_or_vf == 'vf':
                ip_addr = tb_config_obj.get_interface_ipv4_addr(hu, tb_config_obj.get_hu_vf_interface(hu))
            username = tb_config_obj.get_username(hu)
            password = tb_config_obj.get_password(hu)
            desc = 'Scp a file from NU to HU host via {}.'.format(pf_or_vf.upper())
        elif nu_or_hu == hu:
            ip_addr = tb_config_obj.get_interface_ipv4_addr(nu, tb_config_obj.get_a_nu_interface(nu))
            username = tb_config_obj.get_username(hu)
            password = tb_config_obj.get_password(hu)
            desc = 'Scp a file from HU to NU host.'

        collect_stats(when='before')
        result = linux_obj.scp(source_file_path=self.file_name,
                                           target_ip=ip_addr,
                                           target_file_path='{}{}'.format(
                                               self.file_name, '' if not pf_or_vf else pf_or_vf),
                                           target_username=username,
                                           target_password=password,
                                           timeout=60)
        collect_stats(when='after')
        fun_test.test_assert(result, desc)


class FunethTestScpNU2HUPF(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Scp a file from NU to HU host via PF.",
                              steps="""
        1. Scp a file from NU to HU host via PF interface.
        """)

    def setup(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._setup(self, nu, 'pf')

    def run(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._run(self, nu, 'pf')


class FunethTestScpNU2HUVF(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Scp a file from NU to HU host via VF.",
                              steps="""
        1. Scp a file from NU to HU host via VF interface.
        """)

    def setup(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._setup(self, nu, 'vf')

    def run(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._run(self, nu, 'vf')


class FunethTestScpHU2NU(FunethTestScpBase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Scp a file from HU to NU host.",
                              steps="""
        1. Scp a file from HU to NU host.
        """)

    def setup(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._setup(self, hu)

    def run(self):
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        FunethTestScpBase._run(self, hu)


class FunethTestInterfaceFlapBase(FunTestCase):

    def setup(self):
        check_nu_hu_pingable()

    def cleanup(self):
        pass

    def _run(self, pf_or_vf):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj

        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']

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
        verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[interface, ], nu=nu, hu=hu)

        # ifconfig up
        fun_test.test_assert(linux_obj.ifconfig_up_down(interface, action='up', ns=ns),
                             'ifconfig {} up'.format(interface))
        # Need to re-configure route/arp
        fun_test.test_assert(funeth_obj.configure_namespace_ipv4_routes(hu, ns=namespace),
                             'Configure HU host IPv4 routes.')
        verify_nu_hu_datapath(funeth_obj, packet_count=5, packet_size=84, interfaces_excludes=[], nu=nu, hu=hu)


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
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        verify_nu_hu_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'], nu=nu, hu=hu)


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
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        linux_obj = funeth_obj.linux_obj_dict[hu]
        hostname = tb_config_obj.get_hostname(hu)
        fun_test.test_assert(linux_obj.reboot(non_blocking=True), 'Reboot HU host {}'.format(hostname))
        fun_test.sleep("Sleeping for the host to come up from reboot", seconds=300)
        fun_test.test_assert(linux_obj.is_host_up(), 'HU host {} is up'.format(hostname))
        setup_hu_host(funeth_obj, update_driver=False)
        verify_nu_hu_datapath(funeth_obj, nu=nu, hu=hu)


class FunethTestComeReboot(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Reboot COMe.",
                              steps="""
        1. Reboot Come.
        2. Setup control plane.
        3. From NU host, Ping HU host PF/VF interfaces.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        nu = fun_test.shared_variables['sanity_nu']
        hu = fun_test.shared_variables['sanity_hu']
        linux_obj = fun_test.shared_variables["come_linux_obj"]
        hostname = linux_obj.host_ip
        fun_test.test_assert(linux_obj.reboot(non_blocking=True), 'Reboot COMe {}'.format(hostname))
        fun_test.sleep("Sleeping for COMe to come up from reboot", seconds=180)
        fun_test.test_assert(linux_obj.ensure_host_is_up(), 'Come {} is up'.format(hostname))

        tb_config_obj = fun_test.shared_variables['funeth_obj'].tb_config_obj
        pf_interface = tb_config_obj.get_hu_pf_interface(hu)
        vf_interface = tb_config_obj.get_hu_vf_interface(hu)
        verify_nu_hu_datapath(funeth_obj, interfaces_excludes=[pf_interface, vf_interface], nu=nu, hu=hu)

        setup_funcp(fun_test.shared_variables["test_bed_type"], update_funcp=False)
        #setup_hu_host(funeth_obj, update_driver=False)
        verify_nu_hu_datapath(funeth_obj, nu=nu, hu=hu)


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
            FunethTestUnloadDriver,
            FunethTestReboot,
            #FunethTestComeReboot,  # TODO: uncomment after SWLINUX-786 is fixed
    ):
        ts.add_test_case(tc())
    ts.run()
