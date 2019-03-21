from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host.iperf_manager import IPerfManager
from lib.host.netperf_manager import NetperfManager
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
import json
import math


TB = sanity.TB
if TB == 'SN2':
    BW_LIMIT = '7M'
else:
    BW_LIMIT = '25G'
RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
TIMESTAMP = get_current_time()
PARALLEL = 6


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

        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        #fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')
        fun_test.test_assert(self.netperf_manager_obj.cleanup(), 'Clean up')


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
        if flow_type.startswith('NU_HU'):
            linux_obj = funeth_obj.linux_obj_dict['nu']
            if 'VF' in flow_type:
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf)
            else:  # Default use PF interface
                dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.pf_intf)
        elif flow_type.startswith('HU_NU'):
            linux_obj = funeth_obj.linux_obj_dict['hu']
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('nu', funeth_obj.tb_config_obj.get_a_nu_interface())
        elif flow_type.startswith('HU_HU'):
            linux_obj = funeth_obj.linux_obj_dict['hu']
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.vf_intf)
        linux_objs.append(linux_obj)

        if tool == 'netperf':
            perf_manager_obj = NetperfManager(linux_objs)
        else:
            perf_manager_obj = IPerfManager(linux_objs)
        arg_dicts = [
            {'linux_obj': linux_obj,
             'dip': dip,
             'tool': tool,
             'protocol': protocol,
             'parallel': parallel,
             'duration': duration,
             'frame_size': frame_size,
             'bw': bw,
             }
        ]
        if tool == 'netperf':
            for arg_dict in arg_dicts:
                arg_dict.pop('bw')  # 'bw' is n/a in NetperfManager
        result = perf_manager_obj.run(*arg_dicts)

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

# HU -> HU

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

class FunethPerformance_HU_HU_64B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=104,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host PF, run netperf to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=64)


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

class FunethPerformance_HU_NU_64B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=114,
                              summary="Do throughput and latency test of HU -> NU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host, run netperf to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=64)


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

class FunethPerformance_NU_HU_64B_TCP_NETPERF(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=124,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From NU host, run netperf to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', tool='netperf', protocol='tcp', parallel=PARALLEL,
                                   frame_size=64)


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
            FunethPerformance_HU_NU_64B_TCP_NETPERF,
            FunethPerformance_HU_NU_1500B_TCP_NETPERF,

            ## HU -> HU Non-FCP
            #FunethPerformance_HU_HU_800B_UDP_NETPERF,
            #FunethPerformance_HU_HU_64B_UDP_NETPERF,
            #FunethPerformance_HU_HU_1500B_UDP_NETPERF,
            FunethPerformance_HU_HU_800B_TCP_NETPERF,
            FunethPerformance_HU_HU_64B_TCP_NETPERF,
            FunethPerformance_HU_HU_1500B_TCP_NETPERF,
            #
            ## TODO: Add HU -> HU FCP
            #
            ## NU -> HU Non-FCP
            #FunethPerformance_NU_HU_800B_UDP_NETPERF,
            #FunethPerformance_NU_HU_64B_UDP_NETPERF,
            #FunethPerformance_NU_HU_1500B_UDP_NETPERF,
            FunethPerformance_NU_HU_800B_TCP_NETPERF,
            FunethPerformance_NU_HU_64B_TCP_NETPERF,
            FunethPerformance_NU_HU_1500B_TCP_NETPERF,
    ):
        ts.add_test_case(tc())
    ts.run()

    fun_test.log('Performance results:\n{}'.format(RESULT_FILE))
