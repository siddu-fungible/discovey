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

        f1_1_boot_args = "app=hw_hsu_test,tcp_server,rdstest clients=1 msgs=8 --echo --csr-replay localip=29.1.1.2 remoteip=23.1.1.10 " \
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
                                'syn_without_payload', 'syn_with_payload', 'synack_retransmissions', 'synack_retransmission_interval',
                       'duplicate_syn', 'duplicate_syn_after_synack_retransmissions', 'duplicate_syn_diff_seq_num_in_window',
                       'duplicate_syn_diff_seq_num_out_of_window'
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_syn_recvd",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_syn_recvd --ts " + subtests, timeout=600)
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

class Tc3whs(FunTestCase):


    def describe(self):
        self.set_test_details(id=2, summary="Test TCP Three way handshake",
                              steps="""
                                Test scenarios covered:
                                'ack_without_payload', 'ack_with_payload', 'ack_with_push_flag_without_payload',
                       'ack_with_push_flag_with_payload', 'ack_in_future_segment', 'ack_in_past_segment',
                       'rcvnxt_future_segment', 'ack_after_synack_retransmissions', 'unexpected_flags', 'bad_flags',
                       'ack_with_fin_flag_with_payload', 'ack_with_fin_flag_without_payload', 'inorder_ack_after_out_of_order_ack', 'reset_flag', 'reset_ack_flag'
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_3whs",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_3whs --ts " + subtests, timeout=600)
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments --ts " + subtests, timeout=600)
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
                               'ack_without_payload', 'ack_with_payload', 'finack_retransmissions', 'finack_retransmission_interval',
                       'duplicate_client_fin', 'duplicate_client_fin_after_srv_finack_retransmissions', 'duplicate_fin_diff_seq_num',
                       'close_with_reset', 'close_with_reset_ack', 'close_with_ack_future_segment',
                       'close_with_ack_past_segment', 'unexpected_flags', 'bad_flags'
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_last_ack",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_last_ack --ts " + subtests, timeout=600)
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
                                Test scenarios covered:
                                'data_transfer_after_timeout', 'data_transfer_before_timeout', 'out_of_order_ack_before_timeout',
                       'keepalive_before_timeout'
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout --ts " + subtests, timeout=600)
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_traffic_tests --ts send_data1k,send_data10k,send_data25k,send_data1k_drop,send_data10k_drop,send_data25k_drop",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_traffic_tests --ts " + subtests, timeout=600)
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
                                Test scenarios covered:
                                'push_no_ack_without_payload', 'push_no_ack_with_payload', 'ack_with_data_rcvnxt_future_segment', 'ack_with_data_rcvnxt_past_segment',
                       'push_ack_with_data_rcvnxt_future_segment',
                       'push_ack_with_data_rcvnxt_past_segment', 'close_with_reset_and_data', 'close_with_reset_ack_and_data',
                       'close_with_reset_seg', 'close_with_reset_ack_seg', 'close_with_fin_ack_seg', 'close_with_fin_ack_and_data',
                       'close_with_fin_ack_future_segment', 'close_with_fin_ack_past_segment', 'close_with_fin_ack_rcvnxt_past_segment',
                       'close_with_fin_ack_rcvnxt_future_segment', 'close_with_fin_seg', 'close_with_fin_and_data',
                       'close_with_fin_future_segment', 'close_with_fin_past_segment', 'close_with_fin_rcvnxt_past_segment',
                       'close_with_fin_rcvnxt_future_segment',  'unexpected_flags',
                       'bad_flags', 'close_with_reset_ack_future_segment', 'close_with_reset_ack_past_segment',
                       'close_with_reset_ack_rcvnxt_future_segment', 'close_with_reset_ack_rcvnxt_past_segment',
                       'close_with_reset_future_segment', 'close_with_reset_past_segment', 'close_with_reset_rcvnxt_future_segment',
                       'close_with_reset_rcvnxt_past_segment'
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_established",timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_established --ts " + subtests, timeout=600)
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
        self.set_test_details(id=8, summary="Execute non-sanity tests part of tcp_functional.py",
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t " + execute_test,timeout=600)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t " + execute_test + " --ts " + subtests, timeout=600)
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
    if execute_test == 'sanity' or execute_test == 'tc_3whs':
        ts.add_test_case(Tc3whs())
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
    if execute_test not in ('sanity', 'tc_syn_recvd', 'tc_3whs', 'tc_out_of_order_data_segments', 'tc_last_ack', 'tc_keepalive_timeout', 'tc_established', 'tc_traffic_tests' ):
        ts.add_test_case(TcOtherTests())

    ts.run()