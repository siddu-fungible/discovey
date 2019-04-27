from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host.iperf_manager import IPerfManager
from lib.host.netperf_manager import NetperfManager
from lib.host.network_controller import NetworkController
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
import json
import pprint


TB = sanity.TB
if TB == 'SN2':
    BW_LIMIT = '7M'
else:
    BW_LIMIT = '25G'
RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
#RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
TIMESTAMP = get_current_time()
PARALLEL = 8  # TODO: change back to 6 after SWOS-4552 is resolved
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
        #linux_objs = [funeth_obj.linux_obj_dict['nu'], funeth_obj.linux_obj_dict['hu']]
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
    try:
        # TODO: add mpstat and netstat
        for nc_obj in fun_test.shared_variables['network_controller_objs']:
            nc_obj.peek_fpg_port_stats(port_num=0)
            nc_obj.peek_fpg_port_stats(port_num=4)
            #nc_obj.peek_fpg_port_stats(port_num=1)
            #nc_obj.peek_fpg_port_stats(port_num=2)
            nc_obj.peek_psw_global_stats()
            #nc_obj.peek_fcp_global_stats()
            nc_obj.peek_vp_packets()
            #nc_obj.peek_per_vp_stats()
            nc_obj.peek_resource_bam_stats()
            nc_obj.peek_eqm_stats()
            nc_obj.flow_list()
            nc_obj.flow_list(blocked_only=True)
    except:
        pass


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

    def _run(self, flow_type, tool='netperf', protocol='tcp', parallel=1, duration=30, frame_size=800):
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
        collect_stats()
        try:
            result = perf_manager_obj.run(*arg_dicts)
        except:
            result = {}
        fun_test.log('Collect stats after test')
        collect_stats()

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


# iPerf3/owping

# HU -> HU

# UDP

class FunethPerformance_HU_HU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', frame_size=64)


class FunethPerformance_HU_HU_800B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', frame_size=800)


class FunethPerformance_HU_HU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', frame_size=1500)

# TCP


class FunethPerformance_HU_HU_146B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 146B frames of TCP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', protocol='tcp', frame_size=146)


class FunethPerformance_HU_HU_800B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', protocol='tcp', frame_size=800)


class FunethPerformance_HU_HU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', protocol='tcp', frame_size=1500)


# HU -> NU

# UDP

class FunethPerformance_HU_NU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=64)


class FunethPerformance_HU_NU_800B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=800)


class FunethPerformance_HU_NU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=13,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=1500)

# TCP


class FunethPerformance_HU_NU_146B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=14,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 146B frames of TCP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=146)


class FunethPerformance_HU_NU_800B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=15,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=800)


class FunethPerformance_HU_NU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=16,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=1500)


# NU -> HU

# UDP

class FunethPerformance_NU_HU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=21,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=64)


class FunethPerformance_NU_HU_800B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=22,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=800)


class FunethPerformance_NU_HU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=23,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=1500)

# TCP


class FunethPerformance_NU_HU_146B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=24,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 146B frames of TCP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=146)


class FunethPerformance_NU_HU_800B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=25,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=800)


class FunethPerformance_NU_HU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=26,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=1500)


# Netperf

# HU -> HU Non_FCP

# UDP

class FunethPerformance_HU_HU_64B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=101,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=64)


class FunethPerformance_HU_HU_800B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=102,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_1500B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=103,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=1500)

# TCP


class FunethPerformance_HU_HU_128B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=104,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 128B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=128)


class FunethPerformance_HU_HU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=105,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=800)


class FunethPerformance_HU_HU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=106,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=1500)


class FunethPerformance_HU_HU_128B_TCP_NETPERF_MulitipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=107,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 128B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)


class FunethPerformance_HU_HU_800B_TCP_NETPERF_MulitipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=108,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)

class FunethPerformance_HU_HU_1500B_TCP_NETPERF_MulitipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=109,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=1500)

# HU -> NU

# UDP


class FunethPerformance_HU_NU_64B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=111,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=64)


class FunethPerformance_HU_NU_800B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=112,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_NU_1500B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=113,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=1500)

# TCP


class FunethPerformance_HU_NU_128B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=114,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 128B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=128)


class FunethPerformance_HU_NU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=115,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=800)


class FunethPerformance_HU_NU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=116,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=1500)


class FunethPerformance_HU_NU_128B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=117,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 128B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)

class FunethPerformance_HU_NU_800B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=118,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)

class FunethPerformance_HU_NU_1500B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=119,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=1500)
# NU -> HU

# UDP


class FunethPerformance_NU_HU_64B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=121,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=64)


class FunethPerformance_NU_HU_800B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=122,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of UDP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=800)


class FunethPerformance_NU_HU_1500B_UDP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=123,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', parallel=PARALLEL, frame_size=1500)

# TCP


class FunethPerformance_NU_HU_128B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=124,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 128B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=128)


class FunethPerformance_NU_HU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=125,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=800)


class FunethPerformance_NU_HU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=126,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=1,
                                   frame_size=1500)


class FunethPerformance_NU_HU_128B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=127,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 128B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)

class FunethPerformance_NU_HU_800B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=128,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)

class FunethPerformance_NU_HU_1500B_TCP_NETPERF_MultipleFlows(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=129,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=1500)

# HU -> HU FCP

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

    def _run(self, flow_type='HU_HU_FCP', tool='netperf', protocol='tcp', parallel=1, duration=30, frame_size=800,
            bw=BW_LIMIT):
        super(FunethPerformanceFcpBase, self)._run(flow_type=flow_type, tool=tool, protocol=protocol, parallel=parallel,
                                                   duration=duration, frame_size=frame_size, bw=bw)


# UDP

class FunethPerformance_HU_HU_FCP_64B_UDP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=131,
                              summary="Do throughput and latency test of HU -> HU FCP with 64B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=64)


class FunethPerformance_HU_HU_FCP_800B_UDP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=132,
                              summary="Do throughput and latency test of HU -> HU FCP with 800B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_FCP_1500B_UDP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=133,
                              summary="Do throughput and latency test of HU -> HU FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=1500)

# TCP


class FunethPerformance_HU_HU_FCP_128B_TCP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=134,
                              summary="Do throughput and latency test of HU -> HU FCP with 128B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=128)


class FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=135,
                              summary="Do throughput and latency test of HU -> HU FCP with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=800)


class FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=136,
                              summary="Do throughput and latency test of HU -> HU FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=1500)


class FunethPerformance_HU_HU_FCP_128B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=137,
                              summary="Do throughput and latency test of HU -> HU FCP with 128B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=128)


class FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=138,
                              summary="Do throughput and latency test of HU -> HU FCP with 800B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=800)

class FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=139,
                              summary="Do throughput and latency test of HU -> HU FCP with 1500B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=1500)

# HU -> HU FCP secure


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

    def _run(self, flow_type='HU_HU_FCP_SEC', tool='netperf', protocol='tcp', parallel=1, duration=30, frame_size=800,
            bw=BW_LIMIT):
        super(FunethPerformanceFcpSecureBase, self)._run(flow_type=flow_type, tool=tool, protocol=protocol,
                                                         parallel=parallel, duration=duration, frame_size=frame_size,
                                                         bw=bw)

# UDP


class FunethPerformance_HU_HU_FCP_SEC_64B_UDP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=141,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 64B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=64)


class FunethPerformance_HU_HU_FCP_SEC_800B_UDP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=142,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 800B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_FCP_SEC_1500B_UDP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=143,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 1500B frames of UDP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', parallel=PARALLEL, frame_size=1500)

# TCP


class FunethPerformance_HU_HU_FCP_SEC_128B_TCP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=144,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 128B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=128)


class FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=145,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=800)


class FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=146,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 1500B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=1, frame_size=1500)


class FunethPerformance_HU_HU_FCP_SEC_128B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=147,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 128B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=128)


class FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=148,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 800B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF_MultipleFlows(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=149,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 1500B frames of TCP and {} flows".format(PARALLEL),
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=1500)


if __name__ == "__main__":
    ts = FunethPerformance()
    for tc in (

            # iperf3/owping

            ## HU -> NU Non-FCP
            #FunethPerformance_HU_NU_64B_UDP,
            #FunethPerformance_HU_NU_800B_UDP,
            #FunethPerformance_HU_NU_1500B_UDP,
            #FunethPerformance_HU_NU_146B_TCP,
            #FunethPerformance_HU_NU_800B_TCP,
            #FunethPerformance_HU_NU_1500B_TCP,
            #
            ## HU -> HU Non-FCP
            #FunethPerformance_HU_HU_64B_UDP,
            #FunethPerformance_HU_HU_800B_UDP,
            #FunethPerformance_HU_HU_1500B_UDP,
            #FunethPerformance_HU_HU_146B_TCP,
            #FunethPerformance_HU_HU_800B_TCP,
            #FunethPerformance_HU_HU_1500B_TCP,
            #
            ## TODO: Add HU -> HU FCP
            #
            ## NU -> HU Non-FCP
            #FunethPerformance_NU_HU_64B_UDP,
            #FunethPerformance_NU_HU_800B_UDP,
            #FunethPerformance_NU_HU_1500B_UDP,
            #FunethPerformance_NU_HU_146B_TCP,
            #FunethPerformance_NU_HU_800B_TCP,
            #FunethPerformance_NU_HU_1500B_TCP,

            # netperf

            # HU -> NU Non-FCP
            #FunethPerformance_HU_NU_800B_UDP_NETPERF,
            #FunethPerformance_HU_NU_64B_UDP_NETPERF,
            #FunethPerformance_HU_NU_1500B_UDP_NETPERF,
            #FunethPerformance_HU_NU_800B_TCP_NETPERF,
            #FunethPerformance_HU_NU_128B_TCP_NETPERF,
            FunethPerformance_HU_NU_1500B_TCP_NETPERF,
            #FunethPerformance_HU_NU_800B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_HU_NU_128B_TCP_NETPERF_MultipleFlows,
            FunethPerformance_HU_NU_1500B_TCP_NETPERF_MultipleFlows,

            # NU -> HU Non-FCP
            ## FunethPerformance_NU_HU_800B_UDP_NETPERF,
            ## FunethPerformance_NU_HU_64B_UDP_NETPERF,
            ## FunethPerformance_NU_HU_1500B_UDP_NETPERF,
            #FunethPerformance_NU_HU_800B_TCP_NETPERF,
            #FunethPerformance_NU_HU_128B_TCP_NETPERF,
            FunethPerformance_NU_HU_1500B_TCP_NETPERF,
            #FunethPerformance_NU_HU_800B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_NU_HU_128B_TCP_NETPERF_MultipleFlows,
            FunethPerformance_NU_HU_1500B_TCP_NETPERF_MultipleFlows,

            # HU -> HU Non-FCP
            #FunethPerformance_HU_HU_800B_UDP_NETPERF,
            #FunethPerformance_HU_HU_64B_UDP_NETPERF,
            #FunethPerformance_HU_HU_1500B_UDP_NETPERF,
            #FunethPerformance_HU_HU_800B_TCP_NETPERF,
            #FunethPerformance_HU_HU_128B_TCP_NETPERF,
            #FunethPerformance_HU_HU_1500B_TCP_NETPERF,
            #FunethPerformance_HU_HU_800B_TCP_NETPERF_MulitipleFlows,
            #FunethPerformance_HU_HU_128B_TCP_NETPERF_MulitipleFlows,
            #FunethPerformance_HU_HU_1500B_TCP_NETPERF_MulitipleFlows,
            #
            ## HU -> HU FCP non-secure
            ##FunethPerformance_HU_HU_FCP_800B_UDP_NETPERF,
            ##FunethPerformance_HU_HU_FCP_64B_UDP_NETPERF,
            ##FunethPerformance_HU_HU_FCP_1500B_UDP_NETPERF,
            #FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_128B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_HU_HU_FCP_128B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF_MultipleFlows,
            #
            ## HU -> HU FCP secure
            ## FunethPerformance_HU_HU_FCP_SEC_800B_UDP_NETPERF,
            ## FunethPerformance_HU_HU_FCP_SEC_64B_UDP_NETPERF,
            ## FunethPerformance_HU_HU_FCP_SEC_1500B_UDP_NETPERF,
            #FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_SEC_128B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF,
            #FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_HU_HU_FCP_SEC_128B_TCP_NETPERF_MultipleFlows,
            #FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF_MultipleFlows,
    ):
        ts.add_test_case(tc())
    ts.run()

    with open(RESULT_FILE) as f:
        r = json.load(f)
        fun_test.log('Performance results:\n{}'.format(pprint.pformat(r)))
