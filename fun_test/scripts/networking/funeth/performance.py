from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host.iperf_manager import IPerfManager
from lib.host.netperf_manager import NetperfManager
from lib.host.network_controller import NetworkController
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
from collections import OrderedDict
import json
import pprint


TB = sanity.TB
inputs = fun_test.get_job_inputs()
if inputs.get('debug', 0):
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
else:
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
TIMESTAMP = get_current_time()
FLOW_TYPES_DICT = OrderedDict([  # TODO: add FCP
    ('HU_NU_NFCP', 'HU -> NU non-FCP'),
    ('NU_HU_NFCP', 'NU -> HU non-FCP'),
#    ('NU2HU_NFCP', 'NU <-> HU non-FCP'),  # TODO: enable it
#    ('HU_HU_NFCP', 'HU -> HU non-FCP'),
])
TOOLS = ('netperf',)
PROTOCOLS = ('tcp', )  # TODO: add UDP
FRAME_SIZES = (1500,)  # It's actually IP packet size in bytes
NUM_FLOWS = (1, 8,)  # TODO: May add more
FPG_MTU_DEFAULT = 1518
PERF_RESULT_KEYS = ('throughput',
                    'pps',
                    'latency_min',
                    'latency_avg',
                    'latency_max',
                    'latency_P50',
                    'latency_P90',
                    'latency_P99',
                    )
#FPG_INTERFACES = (0, 4,)  # TODO: add fpg4
FPG_INTERFACES = (0,)


class FunethPerformance(sanity.FunethSanity):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU and HU hosts, run netserver
        2. In NU and HU host, do throughput/latency test with 64B/800B/1500B frame sizes - a. NU->HU,  b. HU->NU, c. HU->HU
        """)

    def setup(self):
        super(FunethPerformance, self).setup()

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        linux_objs = funeth_obj.linux_obj_dict.values()
        #self.iperf_manager_obj = IPerfManager(linux_objs)
        self.netperf_manager_obj = NetperfManager(linux_objs)

        #fun_test.test_assert(self.iperf_manager_obj.setup(), 'Set up for throughput/latency test')
        fun_test.test_assert(self.netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        network_controller_objs = []
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT, verbose=True))
        # TODO: create network_controller_obj2 for F1_1
        # Configure small DF/Non-FCP thr to workaround SWOS-4771
        for nc_obj in network_controller_objs:
            buffer_pool_set = nc_obj.set_qos_egress_buffer_pool(df_thr=256,
                                                                nonfcp_thr=256,
                                                                nonfcp_xoff_thr=128,
                                                                mode='nu')
            fun_test.test_assert(buffer_pool_set, 'Configure QoS egress buffer pool')

        fun_test.shared_variables['funeth_obj'] = funeth_obj
        fun_test.shared_variables['network_controller_objs'] = network_controller_objs

    def cleanup(self):
        super(FunethPerformance, self).cleanup()
        #fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')
        fun_test.test_assert(self.netperf_manager_obj.cleanup(), 'Clean up')


def collect_stats():
    # TODO: add mpstat and netstat
    fpg_stats = {}
    for nc_obj in fun_test.shared_variables['network_controller_objs']:
        for i in FPG_INTERFACES:
            r = nc_obj.peek_fpg_port_stats(port_num=i)
            # TODO: handle None
            #if not r:
            #    r = [{}]
            fpg_stats.update(
                {i: r}
            )
        nc_obj.peek_psw_global_stats()
        #nc_obj.peek_fcp_global_stats()
        nc_obj.peek_vp_packets()
        #nc_obj.peek_per_vp_stats()
        #nc_obj.peek_resource_bam_stats()
        #nc_obj.peek_eqm_stats()
        #nc_obj.flow_list()
        #nc_obj.flow_list(blocked_only=True)
    fpg_rx_bytes = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_OctetsReceivedOK'.format(i), 0) for i in FPG_INTERFACES]
    )
    fpg_rx_pkts = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_aFramesReceivedOK'.format(i), 0) for i in FPG_INTERFACES]
    )
    fpg_tx_bytes = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_OctetsTransmittedOK'.format(i), 0) for i in FPG_INTERFACES]
    )
    fpg_tx_pkts = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_aFramesTransmittedOK'.format(i), 0) for i in FPG_INTERFACES]
    )
    return fpg_tx_pkts, fpg_tx_bytes, fpg_rx_pkts, fpg_rx_bytes


def get_fpg_packet_stats():
    pass


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

    def _run(self, flow_type, tool='netperf', protocol='tcp', parallel=1, frame_size=1500, duration=30):
        funeth_obj = fun_test.shared_variables['funeth_obj']

        host_pairs = []
        bi_dir = False
        if flow_type.startswith('HU_HU'):  # HU --> HU
            # TODO: handle exception if hu_hosts len is 1
            for i in range(0, len(funeth_obj.hu_hosts), 2):
                host_pairs.append(funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i+1])
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
                if parallel == 1:
                    break

        #suffixes = ('n2h', 'h2n', 'h2h')  TODO: add 'h2h'
        suffixes = ('n2h', 'h2n')
        arg_dicts = []
        for shost, dhost in host_pairs:
            linux_obj_src = funeth_obj.linux_obj_dict[shost]
            linux_obj_dst = funeth_obj.linux_obj_dict[dhost]
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr(dhost,
                                                                   funeth_obj.tb_config_obj.get_an_interface(dhost))
            suffix = '{}2{}'.format(shost[0], dhost[0])
            arg_dicts.append(
                {'linux_obj': linux_obj_src,
                 'linux_obj_dst': linux_obj_dst,
                 'dip': dip,
                 'tool': tool,
                 'protocol': protocol,
                 'parallel': parallel/len(host_pairs) if not bi_dir else parallel/(len(host_pairs)/2),
                 'duration': duration,
                 'frame_size': frame_size,
                 'suffix': suffix,
                 }
            )

        #linux_objs = [arg_dict.get('linux_obj') for arg_dict in arg_dicts] + [arg_dict.get('linux_obj_dst') for arg_dict in arg_dicts]
        linux_objs = funeth_obj.linux_obj_dict.values()
        perf_manager_obj = NetperfManager(linux_objs)

        # Collect stats before and after test run
        fun_test.log('Collect stats before test')
        fpg_tx_pkts1, _, fpg_rx_pkts1, _ = collect_stats()
        try:
            result = perf_manager_obj.run(*arg_dicts)
        except:
            result = {}
        fun_test.log('Collect stats after test')
        fpg_tx_pkts2, _, fpg_rx_pkts2, _ = collect_stats()

        if flow_type.startswith('NU_HU'):
            result.update(
                {'pps_n2h': (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
            )
        elif flow_type.startswith('NU2HU'):
            result.update(
                {'pps_n2h': (fpg_rx_pkts2 - fpg_rx_pkts1) / duration,
                 'pps_h2n': (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
            )
        elif flow_type.startswith('HU_NU'):
            result.update(
                {'pps_h2n': (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
            )
        elif flow_type.startswith('HU_HU'):
            result.update(
                {'pps_h2h': (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
            )

        # Check test passed or failed
        if any(v == -1 for v in result.values()):
            passed = False
        else:
            passed = True

        # Set -1 for untested direction
        for suffix in suffixes:
            for k in PERF_RESULT_KEYS:
                k_suffix = '{}_{}'.format(k, suffix)
                if k_suffix not in result:
                    result.update(
                        {k_suffix: -1}
                    )

        # Update result dict
        result.update(
            {'flow_type': flow_type,
             'frame_size': frame_size,
             'protocol': protocol.upper(),
             'offloads': False,  # TODO: pass in parameter
             'num_flows': parallel,
             'timestamp': '%s' % TIMESTAMP,  # Use same timestamp for all the results of same run, per John/Ashwin
             'version': fun_test.get_version(),
             }
        )
        fun_test.log('Results:\n{}'.format(pprint.pformat(result)))

        # Update file with result
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.test_assert(passed, 'Get throughput/pps/latency test result')


class FunethPerformanceFcpBase(FunethPerformanceBase):
    def _configure_fpg_mtu(self, mtu):
        network_controller_obj = fun_test.shared_variables['network_controller_obj']
        funeth_obj = fun_test.shared_variables['funeth_obj']
        linux_obj = funeth_obj.linux_obj_dict['nu']

        for intf in funeth_obj.tb_config_obj.get_all_interfaces('nu'):
            fun_test.test_assert(linux_obj.set_mtu(intf, mtu-18), 'Configure NU host interface {} mtu {}'.format(intf, mtu))
            i = int(intf.lstrip('fpg')[0])
            fun_test.test_assert(network_controller_obj.set_port_mtu(i, mtu),
                                 'Configure NU interface {} mtu {}'.format(intf, mtu))

    def setup(self):
        self._configure_fpg_mtu(FPG_MTU_DEFAULT+38)  # 20(IP) + 8(UDP) + 10(FCP) = 38

    def cleanup(self):
        self._configure_fpg_mtu(FPG_MTU_DEFAULT)

    def _run(self, flow_type='HU_HU_FCP', tool='netperf', protocol='tcp', parallel=1, frame_size=800, duration=30):
        super(FunethPerformanceFcpBase, self)._run(flow_type=flow_type, tool=tool, protocol=protocol, parallel=parallel,
                                                   frame_size=frame_size, duration=duration)


class FunethPerformanceFcpSecureBase(FunethPerformanceFcpBase):
    def _configure_fcp_tunnel(self, secure=1):
        network_controller_obj = fun_test.shared_variables['network_controller_obj']
        # TODO: Get FCP tunnel_id from configs instead of hardcoded here
        src_queues = [216, 224]
        dst_queues = [224, 216]
        dst_fteps = [0xB4000301, 0xB4000401]
        if secure:
            remote_key_indexes = [0, 2]
            local_key_indexes = [2, 0]
        else:
            remote_key_indexes = local_key_indexes = [0, 0]

        # Delete FCP tunnel
        for src_queue in src_queues:
            result = network_controller_obj.delete_fcp_tunnel(src_queue=src_queue)
            fun_test.test_assert(result, 'Delete FCP tunnel src_queue {}'.format(src_queue))

        # Create FCP tunnel
        for src_queue, dst_queue, dst_ftep, remote_key_index, local_key_index in zip(src_queues,
                                                                                     dst_queues,
                                                                                     dst_fteps,
                                                                                     remote_key_indexes,
                                                                                     local_key_indexes):
            result = network_controller_obj.create_fcp_tunnel(src_queue=src_queue,
                                                              dst_queue=dst_queue,
                                                              dst_ftep=dst_ftep,
                                                              secure_tunnel=secure,
                                                              remote_key_index=remote_key_index,
                                                              local_key_index=local_key_index)
            fun_test.test_assert(result, 'Configure FCP tunnel src_queue {} dst_queue {} to {}'.format(
                src_queue, dst_queue, 'secure' if secure else 'non-secure'))

    def setup(self):
        super(FunethPerformanceFcpSecureBase, self)._configure_fpg_mtu(FPG_MTU_DEFAULT+66)  # 20(IP) + 8(UDP) + 38(FCP) = 66
        self._configure_fcp_tunnel(secure=1)

    def cleanup(self):
        super(FunethPerformanceFcpSecureBase, self).cleanup()
        self._configure_fcp_tunnel(secure=0)

    def _run(self, flow_type='HU_HU_FCP_SEC', tool='netperf', protocol='tcp', parallel=1, frame_size=800, duration=30):
        super(FunethPerformanceFcpSecureBase, self)._run(flow_type=flow_type, tool=tool, protocol=protocol,
                                                         parallel=parallel, frame_size=frame_size, duration=duration)


def create_testcases(id, summary, steps, flow_type, tool, protocol, num_flow, frame_size):

    class TmpClass(FunethPerformanceBase):

        def describe(self):
            self.set_test_details(id=id, summary=summary, steps=steps)

        def run(self):
            FunethPerformanceBase._run(self, flow_type, tool, protocol, num_flow, frame_size)

    return type('FunethPerformance_{}_{}B_{}_{}_{}flows'.format(flow_type.upper(),
                                                                frame_size,
                                                                protocol.upper(),
                                                                tool.upper(),
                                                                num_flow),
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
                    sub_id_num_flow = sub_id_frame_size
                    for num_flow in NUM_FLOWS:
                        summary = "{}: throughput and latency test by {}, with {}, {}-byte packets and {} flows".format(
                            FLOW_TYPES_DICT.get(flow_type), tool, protocol, frame_size, num_flow
                        )
                        steps = summary
                        tcs.append(create_testcases(
                            sub_id_num_flow, summary, steps, flow_type, tool, protocol, num_flow, frame_size)
                        )
                        #print "id: {}, summary: {}, flow_type: {}, tool: {}, protocol: {}, num_flow: {}, frame_size: {}".format(
                        #    sub_id_num_flow, summary, flow_type, tool, protocol, num_flow, frame_size)
                        sub_id_num_flow += 1
                    sub_id_frame_size += 10
                sub_id_protocol += 100
        id += 1000

    for tc in tcs:
        ts.add_test_case(tc())
    ts.run()

    with open(RESULT_FILE) as f:
        r = json.load(f)
        fun_test.log('Performance results:\n{}'.format(pprint.pformat(r)))
