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
script_timeout = 7200



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
        linux_obj.command("cd /tmp/FunSDK")
        linux_obj.command("git checkout savin/to_commit_master")
        #linux_obj.command("git checkout savin/tcp_perf")
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

        f1_1_boot_args = "app=load_mods rdstype=funtcp cc_huid=2 --csr-replay --dpc-server  --dpc-uart --all_100g " \
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
        time.sleep(120)
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()
        if 'fs' in fun_test.shared_variables:
            fs1 = fun_test.shared_variables['fs']
            fs1.cleanup()


class TcSynSent(FunTestCase):


    def describe(self):
        self.set_test_details(id=1, summary="Test TCP Syn Sent State",
                              steps="""
                                Test scenarios covered:
                                TCP FSM scenarios in syn sent state
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_syn_sent",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py  -b fs -p -t tc_syn_sent --ts " + subtests, timeout=script_timeout)
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


class TcFinWait1(FunTestCase):


    def describe(self):
        self.set_test_details(id=3, summary="Test TCP Fin Wait 1 state",
                              steps="""
                                Test scenarios covered:
                                tc_fin_wait_1
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_fin_wait_1",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_fin_wait_1 --ts " + subtests, timeout=script_timeout )
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

class TcFinWait2(FunTestCase):


    def describe(self):
        self.set_test_details(id=4, summary="Test TCP Fin Wait 2",
                              steps="""
                                Test scenarios covered:
                               TCP Fin Wait 2
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_fin_wait_2",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_fin_wait_2 --ts " + subtests, timeout=script_timeout )
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



class TcClosing(FunTestCase):


    def describe(self):
        self.set_test_details(id=4, summary="Test TCP Closing state",
                              steps="""
                                Test scenarios covered:
                               TCP Closing state
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_closing",timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_closing --ts " + subtests, timeout=script_timeout )
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

    if execute_test == 'sanity' or execute_test == 'tc_syn_sent':
        ts.add_test_case(TcSynSent())
    if execute_test == 'sanity' or execute_test == 'tc_fin_wait_1':
        ts.add_test_case(TcFinWait1())
    if execute_test == 'sanity' or execute_test == 'tc_fin_wait_2':
        ts.add_test_case(TcFinWait2())
    if execute_test == 'sanity' or execute_test == 'tc_closing':
        ts.add_test_case(TcClosing())

    ts.run()