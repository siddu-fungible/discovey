from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host.iperf_manager import IPerfManager
from lib.host.netperf_manager import NetperfManager
from lib.host.network_controller import NetworkController
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
import json
import math
import pprint


TB = sanity.TB
if TB == 'SN2':
    BW_LIMIT = '7M'
else:
    BW_LIMIT = '25G'
#RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
TIMESTAMP = get_current_time()
PARALLEL = 2  # TODO: change back to 6 after SWOS-4552 is resolved
FPG_MTU_DEFAULT = 1518


class FunethPerformance(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU and HU hosts, run netserver
        2. In NU and HU host, do throughput/latency test with 64B/800B/1500B frame sizes - a. NU->HU,  b. HU->NU, c. HU->HU
        """)

    def setup(self):

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        linux_objs = [funeth_obj.linux_obj_dict['nu'], funeth_obj.linux_obj_dict['hu']]
        #self.iperf_manager_obj = IPerfManager(linux_objs)
        self.netperf_manager_obj = NetperfManager(linux_objs)

        #fun_test.test_assert(self.iperf_manager_obj.setup(), 'Set up for throughput/latency test')
        fun_test.test_assert(self.netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        network_controller_obj = NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                   dpc_server_port=sanity.DPC_PROXY_PORT, verbose=True)
        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(sf_thr=4000,
                                                                            sf_xoff_thr=3500,
                                                                            sx_thr=4000,
                                                                            dx_thr=4000,
                                                                            df_thr=4000,
                                                                            fcp_thr=8000,
                                                                            fcp_xoff_thr=7000,
                                                                            nonfcp_thr=8000,
                                                                            nonfcp_xoff_thr=7000,
                                                                            sample_copy_thr=255,
                                                                            mode='nu')
        fun_test.test_assert(buffer_pool_set, 'Configure QoS egress buffer pool')

        fun_test.shared_variables['funeth_obj'] = funeth_obj
        fun_test.shared_variables['network_controller_obj'] = network_controller_obj

    def cleanup(self):
        #fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')
        fun_test.test_assert(self.netperf_manager_obj.cleanup(), 'Clean up')


def collect_stats():
    try:
        network_controller_obj = fun_test.shared_variables['network_controller_obj']
        network_controller_obj.peek_fpg_port_stats(port_num=0)
        network_controller_obj.peek_fpg_port_stats(port_num=1)
        network_controller_obj.peek_fpg_port_stats(port_num=2)
        network_controller_obj.peek_psw_global_stats()
        network_controller_obj.peek_fcp_global_stats()
        network_controller_obj.peek_vp_packets()
        network_controller_obj.peek_per_vp_stats()
        network_controller_obj.peek_resource_bam_stats()
        network_controller_obj.peek_eqm_stats()
        network_controller_obj.flow_list()
        network_controller_obj.flow_list(blocked_only=True)
    except:
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

    def _run(self, flow_type, tool='iperf3', protocol='udp', parallel=1, duration=30, frame_size=800, bw=BW_LIMIT):

        funeth_obj = fun_test.shared_variables['funeth_obj']

        linux_objs = []
        linux_objs_dst = []
        ns_dst_list = []
        if flow_type.startswith('NU_HU'):
            linux_obj = funeth_obj.linux_obj_dict['nu']
            linux_obj_dst = funeth_obj.linux_obj_dict['hu']
            ns = None
            ns_dst = None
            if 'VF' in flow_type:
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf)
                sip = None
            else:  # Default use PF interface
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.pf_intf)
                sip = None
        elif flow_type.startswith('HU_NU'):
            linux_obj = funeth_obj.linux_obj_dict['hu']
            linux_obj_dst = funeth_obj.linux_obj_dict['nu']
            ns = funeth_obj.tb_config_obj.get_hu_pf_namespace()
            ns_dst = None
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('nu', funeth_obj.tb_config_obj.get_a_nu_interface())
            sip = None
        elif flow_type.startswith('HU_HU'):
            linux_obj = funeth_obj.linux_obj_dict['hu']
            linux_obj_dst = funeth_obj.linux_obj_dict['hu']
            ns = funeth_obj.tb_config_obj.get_hu_pf_namespace()
            ns_dst = funeth_obj.tb_config_obj.get_hu_vf_namespace()
            if flow_type == 'HU_HU_NFCP':
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf)
                sip = None
            elif flow_type.startswith('HU_HU_FCP'):
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu',
                                                                    funeth_obj.tb_config_obj.get_hu_vf_interface_fcp())
                sip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu',
                                                                    funeth_obj.tb_config_obj.get_hu_pf_interface_fcp())
        linux_objs.append(linux_obj)
        linux_objs_dst.append(linux_obj_dst)
        ns_dst_list.append(ns_dst)

        # configure MSS by add iptable rule
        for linux_obj_dst, ns_dst in zip(linux_objs_dst, ns_dst_list):
            cmds = (
                'iptables -t mangle -A POSTROUTING -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss {}'.format(
                    frame_size-18-20-20),
                'iptables -t mangle -L',
            )
            for cmd in cmds:
                if ns_dst:
                    cmd = 'ip netns exec {} {}'.format(ns_dst, cmd)
                linux_obj_dst.sudo_command(cmd)

        if tool == 'netperf':
            perf_manager_obj = NetperfManager(linux_objs)
        else:
            perf_manager_obj = IPerfManager(linux_objs)
        arg_dicts = [
            {'linux_obj': linux_obj,
             'dip': dip,
             'sip': sip,
             'tool': tool,
             'protocol': protocol,
             'parallel': parallel,
             'duration': duration,
             'frame_size': frame_size,
             'bw': bw,
             'ns': ns
             }
        ]
        if tool == 'netperf':
            for arg_dict in arg_dicts:
                arg_dict.pop('bw')  # 'bw' is n/a in NetperfManager

        # Collect stats before and after test run
        fun_test.log('Collect stats before test')
        collect_stats()
        result = perf_manager_obj.run(*arg_dicts)
        fun_test.log('Collect stats after test')
        collect_stats()

        # Delete iptable rule
        for linux_obj_dst, ns_dst in zip(linux_objs_dst, ns_dst_list):
            cmds = (
                'iptables -t mangle -D POSTROUTING -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss {}'.format(
                    frame_size-18-20-20),
                'iptables -t mangle -L',
            )
            for cmd in cmds:
                if ns_dst:
                    cmd = 'ip netns exec {} {}'.format(ns_dst, cmd)
                linux_obj_dst.sudo_command(cmd)

        # check for 'nan'
        passed = True
        for k, v in result.items():
            if math.isnan(v):
                result[k] = -1  # Update 'NaN' as -1 for infra to process, per John/Ashwin
                passed = False

        result.update(
            {'flow_type': flow_type,
             'frame_size': frame_size,
             'timestamp': '%s' % TIMESTAMP,  # Use same timestamp for all the results of same run, per John/Ashwin
             'version': fun_test.get_version(),
             }
        )
        fun_test.log('Results:\n{}'.format(pprint.pformat(result)))

        # Update file with result
        #if tool != 'netperf':  # TODO: Remove the check
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.test_assert(passed, 'Get throughput/latency test result')


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
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)


class FunethPerformance_HU_HU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=105,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)


class FunethPerformance_HU_HU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=106,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 1500B frames of TCP",
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
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)


class FunethPerformance_HU_NU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=115,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)


class FunethPerformance_HU_NU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=116,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 1500B frames of TCP",
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
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=128)


class FunethPerformance_NU_HU_800B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=125,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 800B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=800)


class FunethPerformance_NU_HU_1500B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=126,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of TCP",
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
                              summary="Do throughput and latency test of HU -> HU FCP with 64B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=128)


class FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=135,
                              summary="Do throughput and latency test of HU -> HU FCP with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF(FunethPerformanceFcpBase):
    def describe(self):
        self.set_test_details(id=136,
                              summary="Do throughput and latency test of HU -> HU FCP with 1500B frames of TCP",
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
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 64B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=128)


class FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=145,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 800B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via FCP tunnel loopback
        """)

    def run(self):
        FunethPerformanceFcpSecureBase._run(self, tool='netperf', protocol='tcp', parallel=PARALLEL, frame_size=800)


class FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF(FunethPerformanceFcpSecureBase):
    def describe(self):
        self.set_test_details(id=146,
                              summary="Do throughput and latency test of HU -> HU FCP secure tunnel with 1500B frames of TCP",
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
            FunethPerformance_HU_NU_800B_TCP_NETPERF,
            FunethPerformance_HU_NU_128B_TCP_NETPERF,
            FunethPerformance_HU_NU_1500B_TCP_NETPERF,

            # NU -> HU Non-FCP
            # FunethPerformance_NU_HU_800B_UDP_NETPERF,
            # FunethPerformance_NU_HU_64B_UDP_NETPERF,
            # FunethPerformance_NU_HU_1500B_UDP_NETPERF,
            FunethPerformance_NU_HU_800B_TCP_NETPERF,
            FunethPerformance_NU_HU_128B_TCP_NETPERF,
            FunethPerformance_NU_HU_1500B_TCP_NETPERF,

            # HU -> HU Non-FCP
            #FunethPerformance_HU_HU_800B_UDP_NETPERF,
            #FunethPerformance_HU_HU_64B_UDP_NETPERF,
            #FunethPerformance_HU_HU_1500B_UDP_NETPERF,
            FunethPerformance_HU_HU_800B_TCP_NETPERF,
            FunethPerformance_HU_HU_128B_TCP_NETPERF,
            FunethPerformance_HU_HU_1500B_TCP_NETPERF,

            # HU -> HU FCP non-secure
            #FunethPerformance_HU_HU_FCP_800B_UDP_NETPERF,
            #FunethPerformance_HU_HU_FCP_64B_UDP_NETPERF,
            #FunethPerformance_HU_HU_FCP_1500B_UDP_NETPERF,
            FunethPerformance_HU_HU_FCP_800B_TCP_NETPERF,
            FunethPerformance_HU_HU_FCP_128B_TCP_NETPERF,
            FunethPerformance_HU_HU_FCP_1500B_TCP_NETPERF,

            # HU -> HU FCP secure
            # FunethPerformance_HU_HU_FCP_SEC_800B_UDP_NETPERF,
            # FunethPerformance_HU_HU_FCP_SEC_64B_UDP_NETPERF,
            # FunethPerformance_HU_HU_FCP_SEC_1500B_UDP_NETPERF,
            FunethPerformance_HU_HU_FCP_SEC_800B_TCP_NETPERF,
            FunethPerformance_HU_HU_FCP_SEC_128B_TCP_NETPERF,
            FunethPerformance_HU_HU_FCP_SEC_1500B_TCP_NETPERF,
    ):
        ts.add_test_case(tc())
    ts.run()

    with open(RESULT_FILE) as f:
        r = json.load(f)
        fun_test.log('Performance results:\n{}'.format(pprint.pformat(r)))
