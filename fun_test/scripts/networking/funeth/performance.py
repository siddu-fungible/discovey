from lib.system.fun_test import *
from lib.host.linux import Linux
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
import json
import re


NU_HOST = 'cadence-pc-3'
HU_HOST = 'cadence-pc-5'
NU_HOST_MGMT_INTF = 'enp10s0'
HU_HOST_MGMT_INTF = 'eth0'
NU_INTF_IP = '19.1.1.1'
HU_PF_INTF_IP = '53.1.1.5'
BW_LIMIT = '100M'
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

        # NU_HOST
        linux_obj = Linux(host_ip=NU_HOST, ssh_username="localadmin", ssh_password="Precious1*")
        linux_obj.command('sudo ifconfig fpg0 mtu 1482')  # TODO: Remove after MTU issue is fixed
        linux_obj.command('sudo ptp4l -i %s -2 &' % NU_HOST_MGMT_INTF)
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
        linux_obj = Linux(host_ip=HU_HOST, ssh_username="localadmin", ssh_password="Precious1*")
        linux_obj.command('sudo ifconfig hu3-f0 mtu 1482')  # TODO: Remove after MTU issue is fixed
        linux_obj.command('sudo ptp4l -i %s -2 &' % HU_HOST_MGMT_INTF)
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
        output = fun_test.shared_variables['nu_linux_obj'].command(
            '%s pscheduler ping %s' % (fun_test.shared_variables['nu_cmd_prefix'], HU_PF_INTF_IP))
        fun_test.test_assert(re.search(r'pScheduler is alive', output) is not None, "NU pscheduler ping HU")

        # From HU host, do pscheduler ping NU host to make sure it's alive
        output = fun_test.shared_variables['hu_linux_obj'].command(
            '%s pscheduler ping %s' % (fun_test.shared_variables['hu_cmd_prefix'], NU_INTF_IP))
        fun_test.test_assert(re.search(r'pScheduler is alive', output) is not None, "HU pscheduler ping NU")

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

    def _run(self, flow_type, dst, throughput_tool='iperf3', duration=10, frame_size=1500):

        def udp_payload(frame_size):
            return frame_size-18-20-8

        if flow_type == 'NU_HU':
            linux_obj_desc = 'nu_linux_obj'
            cmd_prefix_desc = 'nu_cmd_prefix'
        else:
            linux_obj_desc = 'hu_linux_obj'
            cmd_prefix_desc = 'hu_cmd_prefix'
        linux_obj = fun_test.shared_variables[linux_obj_desc]
        cmd_prefix = fun_test.shared_variables[cmd_prefix_desc]

        result = {
            'flow_type': flow_type,
            'frame_size': frame_size,
        }

        # Throughput
        output = linux_obj.command(
            '%s pscheduler task --tool %s throughput -d %s -u -l %s -t %s -b %s' % (
                cmd_prefix, throughput_tool, dst, udp_payload(frame_size), duration, BW_LIMIT), timeout=300)
        match = re.search(r'Summary.*Throughput.*\s+(\S+ [K|M|G]bps)\s+(\d+) / (\d+)\s+Jitter:\s(\S+ [m|u|n]s)', output,
                          re.DOTALL)
        fun_test.test_assert(match, "Measure %s throughput" % flow_type)

        result.update(
            {
                'throughput': match.group(1),
                'pps': (int(match.group(3)) - int(match.group(2)))/duration,
                'jitter': match.group(4),
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
            result.update({k: i[1]})

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
                              summary="Do throughput and latency test of NU -> HU with 64B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU', dst=HU_PF_INTF_IP, frame_size=64)


class FunethPerformance_NU_HU_1500B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Do throughput and latency test of NU -> HU with 1500B frames",
                              steps="""
        1. Connect to NU host, and run pscheduler throughput/latency test with HU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='NU_HU', dst=HU_PF_INTF_IP, frame_size=1500)


class FunethPerformance_HU_NU_64B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Do throughput and latency test of NU <- HU with 64B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU', dst=NU_INTF_IP, frame_size=64)


class FunethPerformance_HU_NU_1500B(FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Do throughput and latency test of NU <- HU with 1500B frames",
                              steps="""
        1. Connect to HU host, and run pscheduler throughput/latency test with NU host interface as destination
        """)

    def run(self):
        FunethPerformanceBase._run(self, flow_type='HU_NU', dst=NU_INTF_IP, frame_size=1500)


if __name__ == "__main__":
    FunethScript = FunethPerformance()
    #FunethScript.add_test_case(FunethPerformance_NU_HU_64B())
    #FunethScript.add_test_case(FunethPerformance_NU_HU_1500B())
    #FunethScript.add_test_case(FunethPerformance_HU_NU_64B())
    FunethScript.add_test_case(FunethPerformance_HU_NU_1500B())
    FunethScript.run()
