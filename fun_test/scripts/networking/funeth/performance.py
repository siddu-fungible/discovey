from lib.system.fun_test import *
from lib.host.linux import Linux
import re


NU_HOST = 'cadence-pc-3'
#HU_HOST = 'cadence-pc-5'
#NU_INTF_IP = '19.1.1.1'
#HU_PF_INTF_IP = '53.1.1.5'
HU_HOST = 'cadence-pc-4'
NU_INTF_IP = 'cadence-pc-3'
HU_PF_INTF_IP = 'cadence-pc-4'
BW_LIMIT = '1M'


class FunethPerformance(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU/HU host, run pscheduler container, and check pscheduler ping
        2. In NU/HU host, start iperf3 server
        3. In NU/HU host, do throughput test - a. NU > HU,  b. HU > NU, c. HU > HU
        4. In NU/HU host, do latency test - a. NU > HU, b. HU > NU, c. HU > HU
        """)

    def setup(self):

        # NU_HOST
        linux_obj = Linux(host_ip=NU_HOST, ssh_username="user", ssh_password="Precious1*")
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

        # From candence-pc-3, do pscheduler ping to make sure it's alive
        fun_test.sleep('Sleep for a while to wait for pscheduler fully up', 5)
        output = fun_test.shared_variables['nu_linux_obj'].command(
            '%s pscheduler ping %s' % (fun_test.shared_variables['nu_cmd_prefix'], HU_HOST))
        fun_test.test_assert(re.search(r'pScheduler is alive', output) is not None, "Run perfsonar/testpoint container")


    def cleanup(self):
        fun_test.shared_variables['nu_linux_obj'].command(
            'docker kill {0}; docker rm {0}'.format(fun_test.shared_variables['nu_container_id']))
        fun_test.shared_variables['hu_linux_obj'].command(
            'docker kill {0}; docker rm {0}'.format(fun_test.shared_variables['hu_container_id']))
        pass


class FunethThroughputBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, host, desc, dst, tool='iperf3'):
        if host == 'hu':
            linux_obj_desc = 'hu_linux_obj'
            cmd_prefix_desc = 'hu_cmd_prefix'
        elif host == 'nu':
            linux_obj_desc = 'nu_linux_obj'
            cmd_prefix_desc = 'nu_cmd_prefix'
        linux_obj = fun_test.shared_variables[linux_obj_desc]
        cmd_prefix = fun_test.shared_variables[cmd_prefix_desc]
        output = linux_obj.command(
            '%s pscheduler task --tool %s throughput -d %s -u -t 30 -b %s' % (cmd_prefix, tool, dst, BW_LIMIT),
            timeout=300)
        match = re.search(r'Summary.*Throughput.*\s+(\S+ [K|M|G]bps).*Jitter:\s(\S+ [m|u|n]s)', output, re.DOTALL)
        fun_test.test_assert(match, "Measure %s throughput" % desc)
        print '%s - Throughput: %s, Jitter: %s' % (desc, match.group(1), match.group(2))


class FunethThroughput_NUtoHU(FunethThroughputBase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect to NU host and do throughput test of NU > HU",
                              steps="""
        1. Run pscheduler throughput test with HU host interface as destination
        """)

    def run(self):
        FunethThroughputBase._run(self, host='nu', desc='NU to HU', dst=HU_PF_INTF_IP)


class FunethThroughput_HUtoNU(FunethThroughputBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Connect to HU host and do throughput test of NU < HU",
                              steps="""
        1. Run pscheduler throughput test with NU host interface as destination
        """)

    def run(self):
        FunethThroughputBase._run(self, host='hu', desc='HU to NU', dst=NU_INTF_IP)


class FunethLatencyBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, host, desc, dst):
        if host == 'hu':
            linux_obj_desc = 'hu_linux_obj'
            cmd_prefix_desc = 'hu_cmd_prefix'
        elif host == 'nu':
            linux_obj_desc = 'nu_linux_obj'
            cmd_prefix_desc = 'nu_cmd_prefix'
        linux_obj = fun_test.shared_variables[linux_obj_desc]
        cmd_prefix = fun_test.shared_variables[cmd_prefix_desc]
        output = linux_obj.command('%s pscheduler task latency -d %s -c 30 -i 1' % (cmd_prefix, dst), timeout=180)
        match = re.findall(r'Delay (Minimum|Maximum|Mean).*?(\S+ [m|u|n]s)', output)
        fun_test.test_assert(match, "Measure %s latency" % desc)
        print '%s - Latency:' % desc
        for i in match:
            print ': '.join(i)


class FunethLatency_NUtoHU(FunethLatencyBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Connect to NU host and do latency test of NU > HU",
                              steps="""
        1. Run pscheduler latency test with HU host interface as destination
        """)

    def run(self):
        FunethLatencyBase._run(self, host='nu', desc='NU to HU', dst=HU_PF_INTF_IP)


class FunethLatency_HUtoNU(FunethLatencyBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Connect to HU host and do latency test of NU < HU",
                              steps="""
        1. Run pscheduler latency test with NU host interface as destination
        """)

    def run(self):
        FunethLatencyBase._run(self, host='hu', desc='HU PF to NU', dst=NU_INTF_IP)


if __name__ == "__main__":
    FunethScript = FunethPerformance()
    FunethScript.add_test_case(FunethThroughput_NUtoHU())
    FunethScript.add_test_case(FunethThroughput_HUtoNU())
    FunethScript.add_test_case(FunethLatency_NUtoHU())
    FunethScript.add_test_case(FunethLatency_HUtoNU())
    FunethScript.run()
