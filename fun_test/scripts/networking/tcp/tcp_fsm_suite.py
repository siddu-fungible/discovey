from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import copy
import re
from lib.topology.topology_helper import TopologyHelper
import os

network_controller_obj = None
nu_lab_handle = None
host_name = "nu-lab-06"
filename = "tcp_functional.py"
git_path = "FunSDK/integration_test/host"
#script_location = "/local-home/localadmin/tcp_fsm/tcp"
script_location = "/tmp/FunSDK/integration_test/host/tcp"
script_results_file = "tcp_functional.results"
hosts_json_file = ASSET_DIR + "/hosts.json"
all_hosts_specs = parse_file_to_json(file_name=hosts_json_file)
host_spec = all_hosts_specs[host_name]
host_username = host_spec["ssh_username"]
host_passwd = host_spec["ssh_password"]
script_timeout = 3600



TIMESTAMP = None

inputs = fun_test.get_job_inputs()
if inputs:
    if 'test' in inputs:
        execute_test = inputs['test']

        if 'subtests' in inputs:
            subtests = inputs['subtests']
        else:
            subtests = 'all'
else:
    execute_test = 'sanity'
    subtests = 'all'



def prepare_server(host, username="localadmin", password="Precious1*"):
    try:
        linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
        linux_obj.command("rm -rf /tmp/FunSDK")
        linux_obj.sudo_command("rm -rf /tmp/pcaps/*")
        linux_obj.command("cd /tmp")
        linux_obj.command("git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK")
        linux_obj.disconnect()
        return True
    except Exception as e:
        fun_test.critical("Error" + e)
        return False


class ScriptSetup(FunTestScript):

    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                              1. BringUP F1_1

                              """)

    def setup(self):

        f1_1_boot_args = "app=hw_hsu_test,tcp_server,rdstest clients=10 msgs=8 --echo --csr-replay localip=29.1.1.2 remoteip=23.1.1.10 " \
                         "rdstype=funtcp cc_huid=2 --dpc-server  --dpc-uart --all_100g " \
                         "--disable-wu-watchdog module_log=network_unit:CRIT"

        topology_t_bed_type = fun_test.get_job_environment_variable('test_bed_type')

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={1: {"boot_args": f1_1_boot_args}}, disable_f1_index=0)

        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
        print "\n\n\n Booting of FS ended \n\n\n"

        # Copy tcp_functional.py to nu-lab-06
        fun_test.test_assert(expression=prepare_server(host=host_name),
                             message="Preparing Host %s for test execution" % host_name)
        fun_test.sleep("Sleeping before start of test", seconds=15)

    def cleanup(self):
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()
        pass

class TcSynRecvd(FunTestCase):


    def describe(self):
        self.set_test_details(id=1, summary="Test TCP Syn Recvd State",
                              steps="""
                                Test scenarios covered:
                                TCP FSM scenarios in syn recvd state
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_syn_recvd",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_syn_recvd --ts " + subtests, timeout=script_timeout)
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()


class TcOutOfOrderSegments(FunTestCase):


    def describe(self):
        self.set_test_details(id=3, summary="Test TCP Out of order segments",
                              steps="""
                                Test scenarios covered:
                                'future_seg_current_rcvnxt', 'future_seg_future_rcvnxt', 'past_seg_current_rcvnxt',
                       'out_of_window_full_right', 'out_of_window_partial_right'
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcLastAck(FunTestCase):


    def describe(self):
        self.set_test_details(id=4, summary="Test TCP Last Ack",
                              steps="""
                                Test scenarios covered:
                               TCP FSM scenarios in Last ACK state
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_last_ack",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_last_ack --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcKeepAliveTimeout(FunTestCase):


    def describe(self):
        self.set_test_details(id=5, summary="Test TCP Keepalive timeout",
                              steps="""
                                TCP Keepalive scenarios
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcTrafficTests(FunTestCase):


    def describe(self):
        self.set_test_details(id=6, summary="Test TCP Traffic tests",
                              steps="""
                                Test scenarios covered:
                                Send 1k, 10k, 25k with and without drops. Check Checksum
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                subtest_list = []
                datalen_list = ['1k', '10k', '25k', '50k', '75k', '100k', '1000k']
                tc_suites = ['', '_drop']
                for size in datalen_list:
                    for tc in tc_suites:
                        subtest_list.append('send_data' + size + tc)
                subt = ','.join(subtest_list)

                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_traffic_tests --ts %s" %(subt),timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_traffic_tests --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()



class TcEstablished(FunTestCase):


    def describe(self):
        self.set_test_details(id=7, summary="Test TCP Established State",
                              steps="""
                               TCP established cases
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_established",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_established --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcFlowControl(FunTestCase):


    def describe(self):
        self.set_test_details(id=8, summary="Test TCP Flow control tests",
                              steps="""
                               TCP flow control cases
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_flow_control",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_flow_control --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcWindowScale(FunTestCase):


    def describe(self):
        self.set_test_details(id=9, summary="Test TCP Window scale tests",
                              steps="""
                               TCP window scale test cases
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_window_scale",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_window_scale --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

class TcOtherTests(FunTestCase):


    def describe(self):
        self.set_test_details(id=10, summary="Execute non-sanity tests part of tcp_functional.py",
                              steps="""
                                Test scenarios covered:
                                Any test not part of Sanity but part of tcp_functional.py
                              """)

    def setup(self):
        try:
            self.linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_passwd)

            self.linux_obj.command("cd " + script_location)
            self.linux_obj.command("rm -rf " + script_results_file)
        except Exception as e:
            fun_test.critical("Error" + e)
            return False
    def run(self):
        try:
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t " + execute_test,timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t " + execute_test + " --ts " + subtests, timeout=script_timeout )
            return True
        except Exception as e:
            fun_test.critical("Error" + e)
            return False

    def cleanup(self):
        results = self.linux_obj.read_file(script_results_file)
        key = ''
        value = False
        m = re.search("(\S+)\s+\|\s+Result\s+:\s+(PASS|FAIL)",results)
        if m:
            key = m.group(1)
            value = m.group(2)
            if value == "FAIL":
                res = False
            else:
                res = True
        fun_test.test_assert(expression=res, message=key + '=' + value)
        self.linux_obj.disconnect()

if __name__ == '__main__':
    ts = ScriptSetup()

    if execute_test == 'sanity' or execute_test == 'tc_syn_recvd':
        ts.add_test_case(TcSynRecvd())
    if execute_test == 'sanity' or execute_test == 'tc_out_of_order_data_segments':
        ts.add_test_case(TcOutOfOrderSegments())
    if execute_test == 'sanity' or execute_test == 'tc_last_ack':
        ts.add_test_case(TcLastAck())
    if execute_test == 'sanity' or execute_test == 'tc_keepalive_timeout':
        ts.add_test_case(TcKeepAliveTimeout())
    if execute_test == 'sanity' or execute_test == 'tc_established':
        ts.add_test_case(TcEstablished())
    if execute_test == 'sanity' or execute_test == 'tc_traffic_tests':
        ts.add_test_case(TcTrafficTests())
    if execute_test == 'sanity' or execute_test == 'tc_window_scale':
        ts.add_test_case(TcWindowScale())
    if execute_test == 'sanity' or execute_test == 'tc_flow_control':
        ts.add_test_case(TcFlowControl())
    if execute_test not in ('sanity', 'tc_syn_recvd', 'tc_out_of_order_data_segments', 'tc_last_ack', 'tc_keepalive_timeout',
                            'tc_established', 'tc_traffic_tests', 'tc_window_scale', 'tc_flow_control'):
        ts.add_test_case(TcOtherTests())

    ts.run()
