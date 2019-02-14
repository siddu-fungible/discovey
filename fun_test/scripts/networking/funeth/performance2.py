from lib.system.fun_test import *
from fun_settings import FUN_TEST_DIR
from lib.host.iperf_manager import IPerfManager
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
import json


TB = sanity.TB
if TB == 'SN2':
    BW_LIMIT = '2M'
else:
    BW_LIMIT = '10G'
RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'


class FunethPerformance(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU and HU hosts, run iperf/iperf3 server and owampd
        2. In NU and HU host, do throughput/latency test with 64B/1500B frame sizes - a. NU->HU,  b. HU->NU, c. HU->HU
        """)

    def setup(self):

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        linux_objs = [funeth_obj.linux_obj_dict['nu'], funeth_obj.linux_obj_dict['hu']]
        self.iperf_manager_obj = IPerfManager(linux_objs)

        fun_test.test_assert(self.iperf_manager_obj.setup(), 'Set up for throughput/latency test')

        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')


class FunethPerformanceBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        fun_test.sleep("Waiting for buffer drain", seconds=60)

    def _run(self, flow_type, tool='iperf3', protocol='udp', parallel=1, duration=10, frame_size=1500, bw=BW_LIMIT):

        funeth_obj = fun_test.shared_variables['funeth_obj']

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

        iperf_manager_obj = IPerfManager([linux_obj])
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
        result = iperf_manager_obj.run(*arg_dicts)
        fun_test.test_assert(result, 'Get throughput/latency test result')
        result.update(
            {'flow_type': flow_type}
        )

        # Update file with result
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)


class FunethPerformance_NU_HU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_PF_NFCP', frame_size=64)


class FunethPerformance_NU_HU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=1500)


class FunethPerformance_NU_HU_64B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=64)


class FunethPerformance_NU_HU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From NU host, run iperf3 to HU host PF interface as destination
        2. From NU host, run owping to HU host PF interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=1500)


class FunethPerformance_HU_NU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=64)


class FunethPerformance_HU_NU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=1500)


class FunethPerformance_HU_NU_64B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=64)


class FunethPerformance_HU_NU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host, run iperf3 to NU host interface as destination
        2. From HU host, run owping to NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=1500)


class FunethPerformance_HU_HU_64B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Do throughput and latency test of HU -> HU Non-FCP with 64B frames of UDP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', frame_size=64)


class FunethPerformance_HU_HU_1500B_UDP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 1500B frames of UDP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', frame_size=1500)


class FunethPerformance_HU_HU_64B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 64B frames of TCP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', protocol='tcp', frame_size=64)


class FunethPerformance_HU_HU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 1500B frames of TCP",
                              steps="""
        1. From HU host PF, run iperf3 to HU host VF interface as destination via NU loopback
        2. From HU host PF, run owping to HU host VF interface as destination via NU loopback
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_HU_NFCP', protocol='tcp', frame_size=1500)


if __name__ == "__main__":
    FunethScript = FunethPerformance()

    # NU -> HU
    #FunethScript.add_test_case(FunethPerformance_NU_HU_64B_UDP())
    #FunethScript.add_test_case(FunethPerformance_NU_HU_1500B_UDP())
    #FunethScript.add_test_case(FunethPerformance_NU_HU_64B_TCP())
    #FunethScript.add_test_case(FunethPerformance_NU_HU_1500B_TCP())

    # HU -> NU
    # TODO: Below throughput result is too small in SN2, need further investigation
    FunethScript.add_test_case(FunethPerformance_HU_NU_64B_UDP())
    FunethScript.add_test_case(FunethPerformance_HU_NU_1500B_UDP())
    FunethScript.add_test_case(FunethPerformance_HU_NU_64B_TCP())
    FunethScript.add_test_case(FunethPerformance_HU_NU_1500B_TCP())

    # HU -> NU
    #FunethScript.add_test_case(FunethPerformance_HU_HU_64B_UDP())
    #FunethScript.add_test_case(FunethPerformance_HU_HU_1500B_UDP())
    #FunethScript.add_test_case(FunethPerformance_HU_HU_64B_TCP())
    #FunethScript.add_test_case(FunethPerformance_HU_HU_1500B_TCP())

    FunethScript.run()
    fun_test.log('Performance results:\n{}'.format(RESULT_FILE))
