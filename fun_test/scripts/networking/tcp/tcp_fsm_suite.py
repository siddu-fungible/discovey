from lib.system.fun_test import *
fun_test.enable_storage_api()
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import copy
import re
import socket
from lib.topology.topology_helper import TopologyHelper
import os
from scripts.storage.storage_helper import *
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from swagger_client.models.body_volume_attach import BodyVolumeAttach
from swagger_client.models.transport import Transport
from swagger_client.rest import ApiException
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes



network_controller_obj = None
nu_lab_handle = None
#host_name = "mktg06"
filename = "tcp_functional.py"
git_path = "FunSDK/integration_test/host"
#script_location = "/local-home/localadmin/tcp_fsm/tcp"
script_location = "/tmp/FunSDK/integration_test/host/tcp"
script_results_file = "tcp_functional.results"
hosts_json_file = ASSET_DIR + "/hosts.json"
all_hosts_specs = parse_file_to_json(file_name=hosts_json_file)





TIMESTAMP = None

inputs = fun_test.get_job_inputs()
if inputs:
    if 'test' in inputs:
        execute_test = inputs['test']

        if 'subtests' in inputs:
            subtests = inputs['subtests']
        else:
            subtests = 'all'
    if 'host_name' in inputs:
        host_name = inputs['host_name']
else:
    execute_test = 'sanity'
    subtests = 'all'

host_spec = all_hosts_specs[host_name]
host_username = host_spec["ssh_username"]
host_passwd = host_spec["ssh_password"]
script_timeout = 7200



def prepare_server(host, username="localadmin", password="Precious1*"):
    try:
        linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
        linux_obj.command("rm -rf /tmp/FunSDK")
        linux_obj.sudo_command("rm -rf /tmp/pcaps/*")
        linux_obj.command("cd /tmp")
        linux_obj.command("git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK")
        linux_obj.command("cd /tmp/FunSDK")
        linux_obj.command("git checkout savin/to_commit_master")
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
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)
        host_info = self.hosts_asset[host_name]
        self.remoteip_raw = host_info['host_ip']
        self.intf = host_info['test_interface_name']
        #self.remoteip = socket.gethostbyname(remoteip_host)
        fun_test.shared_variables["intf"] = self.intf

        client_obj = Linux(host_ip=self.remoteip_raw, ssh_username="localadmin",
                           ssh_password="Precious1*")

        self.client_mac = client_obj.ifconfig(interface=self.intf)[0]["ether"]
        self.remoteip = client_obj.ifconfig(interface=self.intf)[0]["ipv4"]
        fun_test.shared_variables["client_mac"] = self.client_mac
        fun_test.shared_variables["remoteip"] = self.remoteip

        arp_op = client_obj.sudo_command("arp -i {interface}".format(interface=self.intf))
        match_mac_addr = re.search(r'(?P<ether>\w+:\w+:\w+:\w+:\w+:\w+)', arp_op)
        if match_mac_addr:
            self.gw_mac= match_mac_addr.group()
            fun_test.shared_variables["gw_mac"] = self.gw_mac
        else:
            fun_test.test_assert(False,"MAC address for the gateway found")



        topology_t_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        self.already_deployed = True

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(fs_parameters={"already_deployed": self.already_deployed})

        self.topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = self.topology
        fun_test.test_assert(self.topology, "Topology deployed")
        # fun_test.sleep("Waiting For API Server Bringup", seconds=60)
        self.blt_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.blt_template.initialize(already_deployed=self.already_deployed)
        print "\n\n\n Booting of FS ended \n\n\n"
        fs_obj = self.topology.get_dut_instance(index=0)
        self.dpc_f1_0 = fs_obj.get_dpc_client(0)
        target_ip = self.dpc_f1_0.target_ip
        target_port = self.dpc_f1_0.target_port
        localip_raw = fs_obj.networking.get_bond_interface(f1_index=0, interface_index=0)
        self.localip = str(localip_raw.ip).split('/')[0]
        fun_test.shared_variables["localip"] = self.localip
        # server_obj = Linux(host_ip=self.localip, ssh_username="localadmin",
        #                    ssh_password="Precious1*")
        # self.server_mac = server_obj.ifconfig(interface=self.intf)["ether"]
        # fun_test.shared_variables["server_mac"] = self.server_mac

        network_controller_obj = NetworkController(dpc_server_ip=target_ip,
                                                   dpc_server_port=target_port)
        network_controller_obj.execute_rdstest_app(localip=self.localip, remoteip=self.remoteip)
        fun_test.shared_variables['app_index'] = "{COME_IP}_{F1_INDEX}".format(COME_IP=str(self.dpc_f1_0.target_ip),F1_INDEX=str(0))
        # Connect to Come of the F1 which is connected to the host
        # Execute rdstest app
        # Copy tcp_functional.py to nu-lab-06
        fun_test.test_assert(expression=prepare_server(host=host_name),
                             message="Preparing Host %s for test execution" % host_name)
        fun_test.sleep("Sleeping before start of test", seconds=15)


    def cleanup(self):
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()

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
            self.localip = fun_test.shared_variables["localip"]
            self.remoteip = fun_test.shared_variables["remoteip"]
            self.app_index = fun_test.shared_variables['app_index']
            self.intf = fun_test.shared_variables["intf"]
            self.client_mac = fun_test.shared_variables["client_mac"]
            self.gw_mac = fun_test.shared_variables["gw_mac"]
            if subtests == 'all':
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_syn_recvd"
                                            " --smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                    remoteip=self.remoteip,
                    localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                    APP_INDEX=self.app_index),
                    timeout=script_timeout)
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
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments" "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index),
                    timeout=script_timeout)
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_out_of_order_data_segments --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index),
                    timeout=script_timeout)
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_last_ack" "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index),timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_last_ack --ts " + subtests,"--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout","--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -a sink -p -t tc_keepalive_timeout --ts " + subtests,"--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
                datalen_list = ['1k', '10k', '25k', '50k', '75k', '100k']
                tc_suites = ['', '_drop']
                for size in datalen_list:
                    for tc in tc_suites:
                        subtest_list.append('send_data' + size + tc)
                subtest_list.append('send_data1000k')        
                subt = ','.join(subtest_list)

                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_traffic_tests --ts %s" %(subt),"--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_traffic_tests --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
        self.set_test_details(id=11, summary="Test TCP Established State",
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_established","--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_established --ts " + subtests,"--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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

class TcCloseWait(FunTestCase):


    def describe(self):
        self.set_test_details(id=7, summary="Test TCP Close Wait State",
                              steps="""
                               TCP Close wait cases
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_close_wait", "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_close_wait --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_flow_control", "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_flow_control --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t tc_window_scale", "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t tc_window_scale --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
                self.linux_obj.sudo_command("./tcp_functional.py -b fs -p -t " + execute_test, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
            else:
                self.linux_obj.sudo_command(
                    "./tcp_functional.py -b fs -p -t " + execute_test + " --ts " + subtests, "--smac {client_mac} --dmac {gw_mac} --sip {remoteip} --dip {localip} --intf {intf} --app_index {APP_INDEX}".format(
                        remoteip=self.remoteip,
                        localip=self.localip, intf=self.intf, gw_mac=self.gw_mac, client_mac=self.client_mac,
                        APP_INDEX=self.app_index), timeout=script_timeout )
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
    if execute_test == 'sanity' or execute_test == 'short_suites' or execute_test == 'tc_out_of_order_data_segments':
        ts.add_test_case(TcOutOfOrderSegments())
    if execute_test == 'sanity' or execute_test == 'tc_last_ack':
        ts.add_test_case(TcLastAck())
    if execute_test == 'sanity' or execute_test == 'short_suites' or execute_test == 'tc_keepalive_timeout':
        ts.add_test_case(TcKeepAliveTimeout())
    if execute_test == 'sanity' or execute_test == 'tc_established':
        ts.add_test_case(TcEstablished())
    if execute_test == 'sanity' or execute_test == 'tc_close_wait':
        ts.add_test_case(TcCloseWait())
    if execute_test == 'sanity' or execute_test == 'short_suites' or execute_test == 'tc_traffic_tests':
        ts.add_test_case(TcTrafficTests())
    if execute_test == 'sanity' or execute_test == 'short_suites' or execute_test == 'tc_window_scale':
        ts.add_test_case(TcWindowScale())
    if execute_test == 'sanity' or execute_test == 'short_suites' or execute_test == 'tc_flow_control':
        ts.add_test_case(TcFlowControl())
    if execute_test not in ('short_suites', 'sanity', 'tc_syn_recvd', 'tc_out_of_order_data_segments', 'tc_last_ack', 'tc_keepalive_timeout',
                            'tc_established', 'tc_traffic_tests', 'tc_window_scale', 'tc_flow_control', 'tc_close_wait'):
        ts.add_test_case(TcOtherTests())

    ts.run()
