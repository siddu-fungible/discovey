from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from scripts.networking.tb_configs import tb_configs
import funeth, sanity
import json
import re


TB = sanity.TB
BW_LIMIT = '2M'
RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'


class FunethPerformance(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU/HU host, run pscheduler container, and check pscheduler ping
        2. In NU/HU host, start iperf3 server
        3. In NU/HU host, do throughput and latency test with 64B/1500B packets - a. NU -> HU,  b. HU -> NU, c. HU -> HU
        """)

    def setup(self):

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj

        # NU host
        linux_obj = funeth_obj.linux_obj_dict['nu']
        linux_obj.command('sudo ptp4l -i %s -2 &' % funeth_obj.tb_config_obj.get_mgmt_interface('nu'))
        linux_obj.command('sudo phc2sys -a -rr &')
        linux_obj.command('docker run --privileged -d -P --net=host -v "/var/run" perfsonar/testpoint')
        output = linux_obj.command('docker ps')
        match = re.search(r'(\w+)\s+perfsonar/testpoint.*Up', output)
        fun_test.test_assert(match, "Run perfsonar/testpoint container")
        container_id = match.group(1)
        nu_cmd_prefix = 'docker exec -t %s' % container_id
        linux_obj.command('%s iperf3 -sD' % nu_cmd_prefix)
        fun_test.shared_variables['nu_linux_obj'] = linux_obj
        fun_test.shared_variables['nu_cmd_prefix'] = nu_cmd_prefix
        fun_test.shared_variables['nu_container_id'] = container_id

        # HU_HOST
        linux_obj = funeth_obj.linux_obj_dict['hu']
        linux_obj.command('sudo ptp4l -i %s -2 &' % funeth_obj.tb_config_obj.get_mgmt_interface('hu'))
        linux_obj.command('sudo phc2sys -a -rr &')
        linux_obj.command('docker run --privileged -d -P --net=host -v "/var/run" perfsonar/testpoint')
        output = linux_obj.command('docker ps')
        match = re.search(r'(\w+)\s+perfsonar/testpoint.*Up', output)
        fun_test.test_assert(match, "Run perfsonar/testpoint container")
        container_id = match.group(1)
        hu_cmd_prefix = 'docker exec -t %s' % container_id
        linux_obj.command('%s iperf3 -sD' % hu_cmd_prefix)
        fun_test.shared_variables['hu_linux_obj'] = linux_obj
        fun_test.shared_variables['hu_cmd_prefix'] = hu_cmd_prefix
        fun_test.shared_variables['hu_container_id'] = container_id

        # From NU host, do pscheduler ping HU host to make sure it's alive
        fun_test.sleep('Sleep for a while to wait for ptp sync and pscheduler fully up', 10)
        ip_addr = funeth_obj.tb_config_obj.get_interface_ipv4_addr('hu', funeth_obj.pf_intf)
        output = fun_test.shared_variables['nu_linux_obj'].command(
            '%s pscheduler ping %s' % (fun_test.shared_variables['nu_cmd_prefix'], ip_addr))
        fun_test.test_assert(re.search(r'pScheduler is alive', output) is not None, "NU pscheduler ping HU")
        fun_test.shared_variables['hu_ip_addr'] = ip_addr

        # From HU host, do pscheduler ping NU host to make sure it's alive
        intf = funeth_obj.tb_config_obj.get_a_nu_interface()
        ip_addr = funeth_obj.tb_config_obj.get_interface_ipv4_addr('nu', intf)
        output = fun_test.shared_variables['hu_linux_obj'].command(
            '%s pscheduler ping %s' % (fun_test.shared_variables['hu_cmd_prefix'], ip_addr))
        fun_test.test_assert(re.search(r'pScheduler is alive', output) is not None, "HU pscheduler ping NU")
        fun_test.shared_variables['nu_ip_addr'] = ip_addr

        for h in ('nu', 'hu'):
            for cmd in ('ps aux | egrep "ptp|phc" | grep -v grep',
                        'timedatectl status',
                        '%s ps aux' % fun_test.shared_variables['%s_cmd_prefix' % h]):
                fun_test.shared_variables['%s_linux_obj' % h].command(cmd)


    def cleanup(self):
        fun_test.shared_variables['nu_linux_obj'].command(
            'docker kill {0}; docker rm {0}'.format(fun_test.shared_variables['nu_container_id']))
        fun_test.shared_variables['hu_linux_obj'].command(
            'docker kill {0}; docker rm {0}'.format(fun_test.shared_variables['hu_container_id']))
        for cmd in ('sudo pkill ptp4l', 'sudo pkill phc2sys'):
            fun_test.shared_variables['nu_linux_obj'].command(cmd)
            fun_test.shared_variables['hu_linux_obj'].command(cmd)
        pass


class FunethPerformanceBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, flow_type, throughput_tool='iperf3', protocol='udp', parallel=1, duration=10, frame_size=1500):

        def udp_payload(frame_size):
            return frame_size-18-20-8

        def tcp_payload(frame_size):
            return frame_size-18-20-20

        def format_throughput(s):
            """Return throughput in Mbps"""
            if s.endswith('Kbps'):
                factor = 1.0/1000
            elif s.endswith('Mbps'):
                factor = 1.0
            elif s.endswith('Gbps'):
                factor = 1.0*1000
            return float(s.rstrip('KMGbps').strip()) * factor

        def format_latency(s):
            """Return latency in us"""
            if s.endswith('ns'):
                factor = 1.0/1000
            elif s.endswith('us'):
                factor = 1.0
            elif s.endswith('ms'):
                factor = 1.0*1000
            return float(s.rstrip('nums').strip()) * factor

        if flow_type == 'NU_HU':
            linux_obj_desc = 'nu_linux_obj'
            cmd_prefix_desc = 'nu_cmd_prefix'
            dst = fun_test.shared_variables['hu_ip_addr']
        elif flow_type == 'HU_NU':
            linux_obj_desc = 'hu_linux_obj'
            cmd_prefix_desc = 'hu_cmd_prefix'
            dst = fun_test.shared_variables['nu_ip_addr']
        linux_obj = fun_test.shared_variables[linux_obj_desc]
        cmd_prefix = fun_test.shared_variables[cmd_prefix_desc]

        result = {
            'flow_type': flow_type,
            'frame_size': frame_size,
        }

        # Throughput
        if protocol.lower() == 'udp':
            output = linux_obj.command(
                '%s pscheduler task --tool %s throughput -d %s -u -l %s -t %s -b %s -P %s' % (
                    cmd_prefix, throughput_tool, dst, udp_payload(frame_size), duration, BW_LIMIT, parallel),
                timeout=300)
            match = re.search(r'Summary.*Throughput.*\s+(\S+ [K|M|G]bps)\s+(\d+) / (\d+)\s+Jitter:\s(\S+ [m|u|n]s)', output,
                              re.DOTALL)
            fun_test.test_assert(match, "Measure %s throughput" % flow_type)

            result.update(
                {
                    'throughput': format_throughput(match.group(1)),
                    'pps': (float(match.group(3)) - float(match.group(2)))/duration,
                    'jitter': format_latency(match.group(4)),
                }
            )
        elif protocol.lower() == 'tcp':
            output = linux_obj.command(
                '%s pscheduler task --tool %s throughput -d %s -l %s -t %s -P %s' % (
                    cmd_prefix, throughput_tool, dst, tcp_payload(frame_size), duration, parallel), timeout=300)
            match = re.search(r'Summary.*Throughput.*\s+(\S+ [K|M|G]bps)', output, re.DOTALL)
            fun_test.test_assert(match, "Measure %s throughput" % flow_type)

            result.update(
                {
                    'throughput': format_throughput(match.group(1)),
                    #'pps': (int(match.group(3)) - int(match.group(2))) / duration,
                }
            )

        # Latency
        packet_count = duration * result.get('pps', 1)
        packet_interval = float(1)/result.get('pps', 1)
        output = linux_obj.command(
            '%s pscheduler task latency -d %s -p %s -c %s -i %s' % (
                cmd_prefix, dst, udp_payload(frame_size)-14, packet_count, packet_interval),
            timeout=180)
        match = re.findall(r'Delay (Median|Minimum|Maximum|Mean).*?(\S+ [m|u|n]s)', output)
        fun_test.test_assert(match, "Measure %s latency" % flow_type)

        for i in match:
            if i[0] == 'Median':
                k = 'latency_median'
            elif i[0] == 'Minimum':
                k = 'latency_min'
            elif i[0] == 'Maximum':
                k = 'latency_max'
            elif i[0] == 'Mean':
                k = 'latency_mean'
            result.update({k: format_latency(i[1])})

        result.update(
            {'timestamp': '%s' % get_current_time(),
             'version': fun_test.get_version(),
             }
        )

        # Update file with result
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)



class FunethPerformance_NU_HU_64B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 64B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=64)


class FunethPerformance_NU_HU_1500B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Do throughput and latency test of NU -> HU Non-FCP with 1500B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', frame_size=1500)


class FunethPerformance_NU_HU_64B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Do TCP throughput and latency test of NU -> HU Non-FCP with 64B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=64)


class FunethPerformance_NU_HU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Do TCP throughput and latency test of NU -> HU Non-FCP with 1500B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU_NFCP', protocol='tcp', frame_size=1500)


class FunethPerformance_HU_NU_64B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 64B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=64)


class FunethPerformance_HU_NU_1500B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Do throughput and latency test of NU <- HU Non-FCP with 1500B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', frame_size=1500)


class FunethPerformance_HU_NU_64B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Do TCP throughput and latency test of NU <- HU Non-FCP with 64B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=64)


class FunethPerformance_HU_NU_1500B_TCP(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Do TCP throughput and latency test of NU <- HU Non-FCP with 1500B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU_NFCP', protocol='tcp', frame_size=1500)


if __name__ == "__main__":
    FunethScript = FunethPerformance()

    # NU -> HU
    # TODO: Uncomment below after EM-804 is fixed
    #FunethScript.add_test_case(FunethPerformance_NU_HU_64B())
    #FunethScript.add_test_case(FunethPerformance_NU_HU_1500B())
    FunethScript.add_test_case(FunethPerformance_NU_HU_64B_TCP())
    FunethScript.add_test_case(FunethPerformance_NU_HU_1500B_TCP())

    # HU -> NU
    # TODO: Below throughput result is too small in SN2, need further investigation
    #FunethScript.add_test_case(FunethPerformance_HU_NU_64B())
    #FunethScript.add_test_case(FunethPerformance_HU_NU_1500B())
    FunethScript.add_test_case(FunethPerformance_HU_NU_64B_TCP())
    FunethScript.add_test_case(FunethPerformance_HU_NU_1500B_TCP())

    FunethScript.run()
    fun_test.log('Performance results:\n{}'.format(RESULT_FILE))
