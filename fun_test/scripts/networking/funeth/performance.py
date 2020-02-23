from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host import netperf_manager as nm
from lib.host.network_controller import NetworkController
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity, perf_utils
from web.fun_test.analytics_models_helper import get_data_collection_time
from collections import OrderedDict
import json
import pprint


TB = sanity.TB
inputs = fun_test.get_job_inputs()
if inputs:
    debug_mode = (inputs.get('debug', 0) == 1)
else:
    debug_mode = False

#if debug_mode:
#    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
#else:
#    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'

TIMESTAMP = get_data_collection_time()

FLOW_TYPES_DICT = OrderedDict([
    ('HU_NU_NFCP',              'HU -> NU non-FCP'),                        # test case id: 1xxx
    ('NU_HU_NFCP',              'NU -> HU non-FCP'),                        # test case id: 2xxx
    ('HU_HU_NFCP',              'HU -> HU non-FCP under 1 F1'),             # test case id: 3xxx
    ('HU_HU_FCP',               'HU -> HU FCP under 2 F1s'),                # test case id: 4xxx
    ('HU_HU_NFCP_2F1',          'HU -> HU non-FCP under 2 F1s'),            # test case id: 5xxx
    ('HU_NU_NFCP_UL_VM',        'HU -> NU non-FCP'),                        # test case id: 6xxx
    ('NU_HU_NFCP_UL_VM',        'NU -> HU non-FCP'),                        # test case id: 7xxx
    ('HU_HU_NFCP_UL_VM',        'HU -> HU non-FCP under 1 F1'),             # test case id: 8xxx
    ('HU_HU_FCP_UL_VM',         'HU -> HU Underlay FCP under 2 F1s'),       # test case id: 9xxx
    ('HU_HU_NFCP_2F1_UL_VM',    'HU -> HU Underlay non-FCP under 2 F1s'),   # test case id: 10xxx
    ('HU_HU_FCP_OL_VM',         'HU -> HU Overlay FCP under 2 F1s'),        # test case id: 11xxx
    ('HU_HU_NFCP_OL_VM',        'HU -> HU Overlay non-FCP under 2 F1s'),    # test case id: 12xxx
    # TODO: Enable bi-direction
])
TOOLS = ('netperf',)
PROTOCOLS = ('tcp', )  # TODO: add UDP
FRAME_SIZES = (1500,)  # It's actually IP packet size in bytes
NUM_FLOWS = (1, 8, 4, 2, 16, 32)  # TODO: May add more
NUM_HOSTS = (1, 2, )  # Number of PCIe hosts, TODO: may keep 2 hosts only in the future
FPG_MTU_DEFAULT = 1518
PERF_RESULT_KEYS = (nm.THROUGHPUT,
                    nm.PPS,
                    nm.LATENCY_MIN,
                    nm.LATENCY_AVG,
                    nm.LATENCY_MAX,
                    nm.LATENCY_P50,
                    nm.LATENCY_P90,
                    nm.LATENCY_P99,
                    nm.LATENCY_MIN_ULOAD,
                    nm.LATENCY_AVG_ULOAD,
                    nm.LATENCY_MAX_ULOAD,
                    nm.LATENCY_P50_ULOAD,
                    nm.LATENCY_P90_ULOAD,
                    nm.LATENCY_P99_ULOAD,
                    )
FPG_INTERFACES = (0, 4,)
FPG_FABRIC_DICT = {
    'F1_0': (16, 12),
    'F1_1': (12, 20),
}


class FunethPerformance(sanity.FunethSanity):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU and HU hosts, run netserver
        2. In NU and HU host, do throughput/latency test with 64B/800B/1500B frame sizes - a. NU->HU,  b. HU->NU, c. HU->HU
        """)

    def setup(self):
        super(FunethPerformance, self).setup()
        funsdk_commit = super(FunethPerformance, self).__getattribute__('funsdk_commit')
        funsdk_bld = super(FunethPerformance, self).__getattribute__('funsdk_bld')
        driver_commit = super(FunethPerformance, self).__getattribute__('driver_commit')
        driver_bld =  super(FunethPerformance, self).__getattribute__('driver_bld')
        come_linux_obj = super(FunethPerformance, self).__getattribute__('come_linux_obj')
        funeth_obj = super(FunethPerformance, self).__getattribute__('funeth_obj')
        if sanity.csi_perf_enabled or sanity.csi_cache_miss_enabled:
            csi_perf_obj = super(FunethPerformance, self).__getattribute__('csi_perf_obj')
        else:
            csi_perf_obj = None
        threading = super(FunethPerformance, self).__getattribute__('threading')
        fun_test.shared_variables['funsdk_commit'] = funsdk_commit
        fun_test.shared_variables['funsdk_bld'] = funsdk_bld
        fun_test.shared_variables['driver_commit'] = driver_commit
        fun_test.shared_variables['driver_bld'] = driver_bld
        fun_test.shared_variables['come_linux_obj'] = come_linux_obj
        fun_test.shared_variables['csi_perf_obj'] = csi_perf_obj
        fun_test.shared_variables['threading'] = threading

        #tb_config_obj = tb_configs.TBConfigs(TB)
        #funeth_obj = funeth.Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        linux_objs = funeth_obj.linux_obj_dict.values()

        fun_test.log("Configure irq affinity")
        for hu in funeth_obj.hu_hosts:
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='tx', cpu_list=funeth.CPU_LIST_HOST)
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='rx', cpu_list=funeth.CPU_LIST_HOST)

        for nu in funeth_obj.nu_hosts:
            linux_obj = funeth_obj.linux_obj_dict[nu]
            perf_utils.mlx5_irq_affinity(linux_obj)

        netperf_manager_obj = nm.NetperfManager(linux_objs)
        fun_test.shared_variables['netperf_manager_obj'] = netperf_manager_obj
        fun_test.test_assert(netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        # HU host is VM
        if sanity.hu_host_vm:
            #tb_config_obj_ul_vm = tb_configs.TBConfigs(tb_configs.get_tb_name_vm(TB, 'ul'))
            #tb_config_obj_ol_vm = tb_configs.TBConfigs(tb_configs.get_tb_name_vm(TB, 'ol'))
            #funeth_obj_ul_vm = funeth.Funeth(tb_config_obj_ul_vm)
            #funeth_obj_ol_vm = funeth.Funeth(tb_config_obj_ol_vm)
            funeth_obj_ul_vm = super(FunethPerformance, self).__getattribute__('funeth_obj_ul_vm')
            funeth_obj_ol_vm = super(FunethPerformance, self).__getattribute__('funeth_obj_ol_vm')
            fun_test.shared_variables['funeth_obj_ul_vm'] = funeth_obj_ul_vm
            fun_test.shared_variables['funeth_obj_ol_vm'] = funeth_obj_ol_vm

            fun_test.log("Configure irq affinity in underlay VMs")
            for hu in funeth_obj_ul_vm.hu_hosts:
                funeth_obj_ul_vm.configure_irq_affinity(hu, tx_or_rx='tx', cpu_list=funeth.CPU_LIST_VM)
                funeth_obj_ul_vm.configure_irq_affinity(hu, tx_or_rx='rx', cpu_list=funeth.CPU_LIST_VM)

            fun_test.log("Configure irq affinity in overlay VMs")
            for hu in funeth_obj_ol_vm.hu_hosts:
                funeth_obj_ol_vm.configure_irq_affinity(hu, tx_or_rx='tx', cpu_list=funeth.CPU_LIST_VM)
                funeth_obj_ol_vm.configure_irq_affinity(hu, tx_or_rx='rx', cpu_list=funeth.CPU_LIST_VM)

            linux_objs_ul_vm = funeth_obj_ul_vm.linux_obj_dict.values()
            linux_objs_ol_vm = funeth_obj_ol_vm.linux_obj_dict.values()
            netperf_manager_obj_ul_vm = nm.NetperfManager(linux_objs_ul_vm)
            netperf_manager_obj_ol_vm = nm.NetperfManager(linux_objs_ol_vm)
            fun_test.test_assert(netperf_manager_obj_ul_vm.setup(), 'Set up for throughput/latency test with underlay VMs')
            fun_test.test_assert(netperf_manager_obj_ol_vm.setup(), 'Set up for throughput/latency test with overlay VMs')

        network_controller_objs = []
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT, verbose=True))
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT2, verbose=True))
        fun_test.shared_variables['network_controller_objs'] = network_controller_objs
        # Configure small DF/Non-FCP thr to workaround SWOS-4771
        for nc_obj in network_controller_objs:
            f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
            buffer_pool_set = nc_obj.set_qos_egress_buffer_pool(sf_thr=11000,
                                                                sf_xoff_thr=10000,
                                                                nonfcp_thr=11000,
                                                                nonfcp_xoff_thr=10000,
                                                                mode='nu')
            fun_test.test_assert(buffer_pool_set, '{}: Configure QoS egress buffer pool'.format(f1))
            nc_obj.get_qos_egress_buffer_pool()

            for port_num in FPG_INTERFACES:
                port_buffer_set = nc_obj.set_qos_egress_port_buffer(port_num, min_threshold=6000, shared_threshold=16383)
                fun_test.test_assert(port_buffer_set, '{}: Configure QoS egress port {} buffer'.format(f1, port_num))
                nc_obj.get_qos_egress_port_buffer(port_num)

            if sanity.control_plane:
                fpg_mtu = 9000
                for p in (0, 4, 8, 12, 16, 20):
                    port_mtu_set = nc_obj.set_port_mtu(p, fpg_mtu)
                    fun_test.test_assert(port_mtu_set, '{}: Configure FPG{} mtu {}'.format(f1, p, fpg_mtu))

        results = []
        fun_test.shared_variables['results'] = results

    def cleanup(self):
        try:
            fs_name = fun_test.get_job_environment_variable('test_bed_type')

            if fs_name == 'fs-11' and sanity.control_plane:
                from scripts.networking.funcp.helper import *
                fs_spec = fun_test.get_asset_manager().get_fs_spec(fs_name)
                funcp_obj = FunControlPlaneBringup(fs_name)

                cc_dmesg(docker_names=funcp_obj.docker_names, fs_spec=fs_spec)
                cc_cc_ethtool_stats_fpg_all(docker_names=funcp_obj.docker_names, fs_spec=fs_spec)
        except Exception as e:
                print(e)

        try:
            results = fun_test.shared_variables['results']
            if not debug_mode:
                perf_utils.db_helper(results)
            perf_utils.populate_result_summary(tc_ids,
                                               results,
                                               fun_test.shared_variables['funsdk_commit'],
                                               fun_test.shared_variables['funsdk_bld'],
                                               fun_test.shared_variables['driver_commit'],
                                               fun_test.shared_variables['driver_bld'],
                                               '00_summary_of_results.txt')
            for nc_obj in fun_test.shared_variables['network_controller_objs']:
                nc_obj.disconnect()
        except:
            pass
        super(FunethPerformance, self).cleanup()
        #fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')
        fun_test.test_assert(fun_test.shared_variables['netperf_manager_obj'].cleanup(), 'Clean up')


tc_ids = []


class FunethPerformanceBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, flow_type, tool='netperf', protocol='tcp', num_flows=1, num_hosts=1, frame_size=1500, duration=30):
        # Underlay VMs
        if 'UL_VM' in flow_type.upper():
            funeth_obj = fun_test.shared_variables['funeth_obj_ul_vm']
            if flow_type.startswith('HU_NU'):
                cpu_list_client = funeth.CPU_LIST_VM
                cpu_list_server = funeth.CPU_LIST_HOST
            elif flow_type.startswith('NU_HU'):
                cpu_list_client = funeth.CPU_LIST_HOST
                cpu_list_server = funeth.CPU_LIST_VM
            elif flow_type.startswith('HU_HU'):
                cpu_list_client = funeth.CPU_LIST_VM
                cpu_list_server = funeth.CPU_LIST_VM
        # Overlay VMs
        elif 'OL_VM' in flow_type.upper():
            funeth_obj = fun_test.shared_variables['funeth_obj_ol_vm']
            cpu_list_client = funeth.CPU_LIST_VM
            cpu_list_server = funeth.CPU_LIST_VM
        # Hosts
        else:
            funeth_obj = fun_test.shared_variables['funeth_obj']
            cpu_list_client = funeth.CPU_LIST_HOST
            cpu_list_server = funeth.CPU_LIST_HOST

        # Tear down FCP tunnel
        # TODO: Need to set up FCP tunnel
        if flow_type.startswith('HU_HU_NFCP_2F1') or flow_type.startswith('HU_HU_NFCP_OL'):
            perf_utils.redis_del_fcp_ftep(fun_test.shared_variables['come_linux_obj'])

        # host/VM use same perf_manager_obj, since CPU tuning is only doable in host
        perf_manager_obj = fun_test.shared_variables['netperf_manager_obj']

        host_pairs = []
        bi_dir = False  # TODO: enable bi-direction
        if flow_type.startswith('HU_HU'):  # HU --> HU
            # TODO: handle exception if hu_hosts len is 1
            num_hu_hosts = len(funeth_obj.hu_hosts)
            flow_types_2f1 = ('HU_HU_NFCP_2F1', 'HU_HU_NFCP_OL', 'HU_HU_FCP')
            if any(flow_type.startswith(f) for f in flow_types_2f1):  # Under 2 F1s
                for i in range(0, num_hu_hosts/2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i+2]])
                    if num_flows == 1:
                        break
                    elif len(host_pairs) == num_hosts:
                        break
            elif flow_type.startswith('HU_HU_NFCP'):  # Under 1 F1
                for i in range(0, num_hu_hosts, 2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i+1]])
                    if num_flows == 1:
                        break
                    elif len(host_pairs) == num_hosts:
                        break
        else:
            for nu, hu in zip(funeth_obj.nu_hosts, funeth_obj.hu_hosts):
                if flow_type.startswith('NU_HU'):  # NU --> HU
                    host_pairs.append([nu, hu])
                elif flow_type.startswith('HU_NU'):  # HU --> NU
                    host_pairs.append([hu, nu])
                elif flow_type.startswith('NU2HU'):  # NU <-> HU
                    host_pairs.append([nu, hu])
                    host_pairs.append([hu, nu])
                    bi_dir = True
                if num_flows == 1:
                    break
                elif len(host_pairs) == num_hosts:
                    break

        suffixes = ('n2h', 'h2n', 'h2h')
        arg_dicts = []
        pingable = True
        for shost, dhost in host_pairs:
            linux_obj_src = funeth_obj.linux_obj_dict[shost]
            linux_obj_dst = funeth_obj.linux_obj_dict[dhost]
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr(dhost,
                                                                   funeth_obj.tb_config_obj.get_an_interface(dhost))

            # Check dip pingable - IP header 20B, ICMP header 8B
            # Allow up to 2 ping miss due to resolve ARP
            if not 'OL_VM' in flow_type.upper():  # TODO: Remove after overlay support ping flow
                pingable &= linux_obj_src.ping(dip, count=5, max_percentage_loss=40, size=frame_size-20-8)

                if pingable:
                    fun_test.test_assert(pingable, '{} ping {} with packet size {}'.format(
                        linux_obj_src.host_ip, dip, frame_size))
                else:
                    break

            suffix = '{}2{}'.format(shost[0], dhost[0])
            arg_dicts.append(
                {'linux_obj': linux_obj_src,
                 'linux_obj_dst': linux_obj_dst,
                 'dip': dip,
                 'tool': tool,
                 'protocol': protocol,
                 #'num_flows': num_flows/len(host_pairs) if not bi_dir else num_flows/(len(host_pairs)/2),
                 'num_flows': num_flows,
                 'duration': duration,
                 'frame_size': frame_size + 18,  # Pass Ethernet frame size
                 'suffix': suffix,
                 'cpu_list_server': cpu_list_server,
                 'cpu_list_client': cpu_list_client,
                 'fixed_netperf_port': True if 'OL_VM' in flow_type.upper() else False,  # TODO: Remove after SWOS-5645
                 'csi_perf_obj': fun_test.shared_variables['csi_perf_obj'],
                 'threading': fun_test.shared_variables['threading'],
                 }
            )

        # Collect stats before and after test run
        network_controller_objs = fun_test.shared_variables['network_controller_objs']
        fpg_interfaces = FPG_INTERFACES[:num_hosts]
        fpg_intf_dict = FPG_FABRIC_DICT
        version = fun_test.get_version()
        fun_test.log('Collect stats before test')
        sth_stuck_before = perf_utils.collect_dpc_stats(network_controller_objs,
                                                        fpg_interfaces,
                                                        fpg_intf_dict,
                                                        version,
                                                        when='before')

        if pingable and not any(i for i in sth_stuck_before[:-1]):  # Still test if is_wropkt_timeout_skip is True

            # TODO: calculate dpc stats collection duration and add it to test duration*2
            perf_utils.collect_host_stats(funeth_obj, version, when='before', duration=duration*5)

            result = perf_manager_obj.run(*arg_dicts)

            fun_test.log('Collect stats after test')
            sth_stuck_after = perf_utils.collect_dpc_stats(network_controller_objs,
                                                           fpg_interfaces,
                                                           fpg_intf_dict,
                                                           version,
                                                           when='after')
            # Collect host stats after dpc stats to give enough time for mpstat collection
            perf_utils.collect_host_stats(funeth_obj, version, when='after')
            #if any(i for i in sth_stuck_after):
            #    result = {}
        else:
            result = {}

        #if result:  # Only if perf_manager has valid result, we update pps; otherwise, it's meaningless
        #    if flow_type.startswith('NU_HU') and result.get('{}_n2h'.format(nm.THROUGHPUT)) != nm.NA:
        #        result.update(
        #            {'{}_n2h'.format(nm.PPS): (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
        #        )
        #    elif flow_type.startswith('NU2HU'):
        #        if result.get('{}_n2h'.format(nm.THROUGHPUT)) != nm.NA:
        #            result.update(
        #                {'{}_n2h'.format(nm.PPS): (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
        #            )
        #        if result.get('{}_h2n'.format(nm.THROUGHPUT)) != nm.NA:
        #            result.update(
        #                {'{}_h2n'.format(nm.PPS): (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
        #            )
        #    elif flow_type.startswith('HU_NU') and result.get('{}_h2n'.format(nm.THROUGHPUT)) != nm.NA:
        #        result.update(
        #            {'{}_h2n'.format(nm.PPS): (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
        #        )
        #    elif flow_type.startswith('HU_HU') and result.get('{}_h2h'.format(nm.THROUGHPUT)) != nm.NA:
        #        # HU -> HU via local F1, no FPG stats
        #        # HU -> HU via FCP, don't check FPG stats as it includes FCP request/grant pkts
        #        result.update(
        #            {'{}_h2h'.format(nm.PPS): nm.calculate_pps(protocol, frame_size, result['throughput_h2h'])}
        #        )

        # Check test passed or failed
        fun_test.log('NetperfManager Results:\n{}'.format(pprint.pformat(result)))
        if not result:
            passed = False
        elif any(v == nm.NA for v in result.values()):
            passed = False
        else:
            passed = True

        # Set N/A for untested direction
        for suffix in suffixes:
            for k in PERF_RESULT_KEYS:
                k_suffix = '{}_{}'.format(k, suffix)
                if k_suffix not in result:
                    result.update(
                        {k_suffix: nm.NA}
                    )

        # Update result dict
        result.update(
            {'flow_type': flow_type,
             'frame_size': frame_size,
             'protocol': protocol.upper(),
             'offloads': sanity.enable_tso,
             'num_flows': num_flows,
             'num_hosts': num_hosts,
             'timestamp': '%s' % TIMESTAMP,  # Use same timestamp for all the results of same run, per John/Ashwin
             'version': version,
             }
        )
        fun_test.log('Final Results:\n{}'.format(pprint.pformat(result)))

        ## Update file with result
        #with open(RESULT_FILE) as f:
        #    r = json.load(f)
        #    r.append(result)
        #
        #with open(RESULT_FILE, 'w') as f:
        #    json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.shared_variables['results'].append(result)
        tc_ids.append(fun_test.current_test_case_id)
        fun_test.simple_assert(pingable, '{} ping {} with packet size {}'.format(
            linux_obj_src.host_ip, dip, frame_size))

        # Check if something is stuck/blocked, or unexpected
        when = 'before'
        for is_etp_queue_stuck, is_flow_blocked, is_parser_stuck, is_vp_stuck, is_wropkt_timeout_skip in (
                sth_stuck_before, sth_stuck_after):
            fun_test.simple_assert(not is_etp_queue_stuck, 'ETP queue is stuck {} test'.format(when))
            fun_test.simple_assert(not is_flow_blocked, 'Flow is blocked {} test'.format(when))
            fun_test.simple_assert(not is_parser_stuck, 'Parser is stuck {} test'.format(when))
            fun_test.simple_assert(not is_vp_stuck, 'VP is stuck {} test'.format(when))
            fun_test.simple_assert(not is_wropkt_timeout_skip, 'WROPKT_TIMEOUT_SKIP happens {} test'.format(when))
            when = 'after'

        fun_test.test_assert(passed, 'Get throughput/pps/latency test result')


def create_testcases(id, summary, steps, flow_type, tool, protocol, num_flows, num_hosts, frame_size):

    class TmpClass(FunethPerformanceBase):

        def describe(self):
            self.set_test_details(id=id, summary=summary, steps=steps)

        def run(self):
            FunethPerformanceBase._run(self, flow_type, tool, protocol, num_flows, num_hosts, frame_size)

    return type('FunethPerformance_{}_{}B_{}_{}_{}flows'.format(flow_type.upper(),
                                                                frame_size,
                                                                protocol.upper(),
                                                                tool.upper(),
                                                                num_flows,
                                                                num_hosts),
                (TmpClass,), {})


if __name__ == "__main__":
    ts = FunethPerformance()
    tcs = []
    id = 1000  # x... - flow_type, .x.. - protocol, ..x. - frame size, ...x - num of flows
    for flow_type in FLOW_TYPES_DICT:
        for tool in TOOLS:
            sub_id_protocol = id
            for protocol in PROTOCOLS:
                sub_id_frame_size = sub_id_protocol
                for frame_size in FRAME_SIZES:
                    sub_id_num_flows = sub_id_frame_size
                    for num_flows in NUM_FLOWS:
                        for num_hosts in NUM_HOSTS:
                            if 'VM' in flow_type.upper():
                                host_desc = 'VMs'
                            else:
                                host_desc = 'hosts'
                            summary = "{}: performance test by {}, with {}, {}-byte packets and {} flows {} {} PCIe {}".format(
                                FLOW_TYPES_DICT.get(flow_type),
                                tool,
                                protocol,
                                frame_size,
                                num_flows,
                                'from' if flow_type.startswith('HU') else 'to',
                                num_hosts,
                                host_desc
                            )
                            steps = summary
                            #print sub_id_num_flows, summary
                            tcs.append(create_testcases(
                                sub_id_num_flows, summary, steps, flow_type, tool, protocol, num_flows, num_hosts, frame_size)
                            )
                            sub_id_num_flows += 1
                            if num_flows == 1 or flow_type in ('HU_HU_NFCP', 'HU_HU_NFCP_UL_VM'):  # Under 1 F1
                                break
                    sub_id_frame_size += 10
                sub_id_protocol += 100
        id += 1000

    for tc in tcs:
        ts.add_test_case(tc())
    ts.run()

