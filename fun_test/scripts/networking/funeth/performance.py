from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host import netperf_manager as nm
from lib.host.network_controller import NetworkController
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity, perf_utils
from collections import OrderedDict
import json
import pprint


TB = sanity.TB
inputs = fun_test.get_job_inputs()
if inputs and inputs.get('debug', 0):
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
else:
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
TIMESTAMP = get_current_time()
FLOW_TYPES_DICT = OrderedDict([  # TODO: add FCP
    ('HU_NU_NFCP', 'HU -> NU non-FCP'), # test case id: 1xxxx
    ('NU_HU_NFCP', 'NU -> HU non-FCP'), # test case id: 2xxxx
    ('HU_HU_NFCP', 'HU -> HU non-FCP'), # test case id: 3xxxx
    ('HU_HU_FCP', 'HU -> HU FCP'),      # test case id: 4xxxx
#    ('NU2HU_NFCP', 'NU <-> HU non-FCP'),  # TODO: enable it
])
TOOLS = ('netperf',)
PROTOCOLS = ('tcp', )  # TODO: add UDP
FRAME_SIZES = (1500,)  # It's actually IP packet size in bytes
NUM_FLOWS = (1, 8, )  # TODO: May add more
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
        fun_test.shared_variables['funsdk_commit'] = funsdk_commit
        fun_test.shared_variables['funsdk_bld'] = funsdk_bld
        fun_test.shared_variables['driver_commit'] = driver_commit
        fun_test.shared_variables['driver_bld'] = driver_bld

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        linux_objs = funeth_obj.linux_obj_dict.values()

        fun_test.log("Configure irq affinity")
        for hu in funeth_obj.hu_hosts:
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='tx')
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='rx')

        netperf_manager_obj = nm.NetperfManager(linux_objs)
        fun_test.shared_variables['netperf_manager_obj'] = netperf_manager_obj
        fun_test.test_assert(netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        network_controller_objs = []
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT, verbose=True))
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT2, verbose=True))
        fun_test.shared_variables['network_controller_objs'] = network_controller_objs
        # Configure small DF/Non-FCP thr to workaround SWOS-4771
        for nc_obj in network_controller_objs:
            f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
            #buffer_pool_set = nc_obj.set_qos_egress_buffer_pool(df_thr=256,
            #                                                    nonfcp_thr=256,
            #                                                    nonfcp_xoff_thr=128,
            #                                                    mode='nu')
            #fun_test.test_assert(buffer_pool_set, '{}: Configure QoS egress buffer pool'.format(f1))

            if sanity.control_plane:
                fpg_mtu = 9000
                for p in (0, 4, 8, 12, 16, 20):
                    port_mtu_set = nc_obj.set_port_mtu(p, fpg_mtu)
                    fun_test.test_assert(port_mtu_set, '{}: Configure FPG{} mtu {}'.format(f1, p, fpg_mtu))

        results = []
        fun_test.shared_variables['results'] = results

    def cleanup(self):
        perf_utils.populate_result_summary(tc_ids,
                                           fun_test.shared_variables['results'],
                                           fun_test.shared_variables['funsdk_commit'],
                                           fun_test.shared_variables['funsdk_bld'],
                                           fun_test.shared_variables['driver_commit'],
                                           fun_test.shared_variables['driver_bld'],
                                           '00_summary_of_results.txt')
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
        if TB == 'SN2':
            interval = 60
        else:
            interval = 5
        fun_test.sleep("Waiting for buffer drain to run next test case", seconds=interval)

    def _run(self, flow_type, tool='netperf', protocol='tcp', num_flows=1, num_hosts=1, frame_size=1500, duration=30):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        perf_manager_obj = fun_test.shared_variables['netperf_manager_obj']

        host_pairs = []
        bi_dir = False
        if flow_type.startswith('HU_HU'):  # HU --> HU
            # TODO: handle exception if hu_hosts len is 1
            num_hu_hosts = len(funeth_obj.hu_hosts)
            if flow_type == 'HU_HU_NFCP':
                for i in range(0, num_hu_hosts, 2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i+1]])
                    if num_flows == 1:
                        break
                    elif len(host_pairs) == num_hosts:
                        break
            elif flow_type == 'HU_HU_FCP':
                for i in range(0, num_hu_hosts/2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i + 2]])
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
        for shost, dhost in host_pairs:
            linux_obj_src = funeth_obj.linux_obj_dict[shost]
            linux_obj_dst = funeth_obj.linux_obj_dict[dhost]
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr(dhost,
                                                                   funeth_obj.tb_config_obj.get_an_interface(dhost))

            # Check dip pingable - IP header 20B, ICMP header 8B
            # Allow up to 2 ping miss due to resolve ARP
            ping_result = linux_obj_src.ping(dip, count=5, max_percentage_loss=40, size=frame_size-20-8)

            fun_test.test_assert(ping_result, '{} ping {} with packet size {}'.format(
                linux_obj_src.host_ip, dip, frame_size))

            suffix = '{}2{}'.format(shost[0], dhost[0])
            arg_dicts.append(
                {'linux_obj': linux_obj_src,
                 'linux_obj_dst': linux_obj_dst,
                 'dip': dip,
                 'tool': tool,
                 'protocol': protocol,
                 'num_flows': num_flows/len(host_pairs) if not bi_dir else num_flows/(len(host_pairs)/2),
                 'duration': duration,
                 'frame_size': frame_size + 18,  # Pass Ethernet frame size
                 'suffix': suffix,
                 }
            )

        # Collect stats before and after test run
        network_controller_objs = fun_test.shared_variables['network_controller_objs']
        fpg_interfaces = FPG_INTERFACES[:num_hosts]
        fpg_intf_dict = FPG_FABRIC_DICT
        funeth_obj = fun_test.shared_variables['funeth_obj']
        version = fun_test.get_version()
        fun_test.log('Collect stats before test')
        fpg_tx_pkts1, _, fpg_rx_pkts1, _ = perf_utils.collect_dpc_stats(network_controller_objs,
                                                                        fpg_interfaces,
                                                                        fpg_intf_dict,
                                                                        version,
                                                                        when='before')
        perf_utils.collect_host_stats(funeth_obj, version, when='before', duration=duration+10)

        result = perf_manager_obj.run(*arg_dicts)

        fun_test.log('Collect stats after test')
        perf_utils.collect_host_stats(funeth_obj, version, when='after')
        fpg_tx_pkts2, _, fpg_rx_pkts2, _ = perf_utils.collect_dpc_stats(network_controller_objs,
                                                                        fpg_interfaces,
                                                                        fpg_intf_dict,
                                                                        version,
                                                                        when='after')

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

        # Update file with result
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.test_assert(passed, 'Get throughput/pps/latency test result')
        fun_test.shared_variables['results'].append(result)
        tc_ids.append(fun_test.current_test_case_id)


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
                            summary = "{}: performance test by {}, with {}, {}-byte packets and {} flows {} {} PCIe hosts".format(
                                FLOW_TYPES_DICT.get(flow_type),
                                tool,
                                protocol,
                                frame_size,
                                num_flows,
                                'from' if flow_type.startswith('HU') else 'to',
                                num_hosts
                            )
                            steps = summary
                            #print sub_id_num_flows, summary
                            tcs.append(create_testcases(
                                sub_id_num_flows, summary, steps, flow_type, tool, protocol, num_flows, num_hosts, frame_size)
                            )
                            sub_id_num_flows += 1
                            if num_flows == 1 or flow_type == 'HU_HU_NFCP':
                                break
                    sub_id_frame_size += 10
                sub_id_protocol += 100
        id += 1000

    for tc in tcs:
        ts.add_test_case(tc())
    ts.run()

    with open(RESULT_FILE) as f:
        r = json.load(f)
        fun_test.log('Performance results:\n{}'.format(pprint.pformat(r)))
