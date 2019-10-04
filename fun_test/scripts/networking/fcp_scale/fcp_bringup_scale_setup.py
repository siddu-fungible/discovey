from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from lib.host.linux import Linux
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import FunCpDockerContainer
import time
import datetime

CHECK_HPING3_ON_HOSTS = True


def clean_testbed(fs_name, hu_host_list):
    funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
    funcp_obj.cleanup_funcp()
    for server in hu_host_list:
        critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")


class FunCPSetup:

    def __init__(self, f1_0_mpg, f1_1_mpg, test_bed_type, abstract_config_f1_0, abstract_config_f1_1,
                 update_funcp=False):
        self.funcp_obj = FunControlPlaneBringup(fs_name=test_bed_type)
        self.update_funcp = update_funcp
        self.f1_0_mpg = f1_0_mpg
        self.f1_1_mpg = f1_1_mpg
        self.abstract_config_f1_0 = abstract_config_f1_0
        self.abstract_config_f1_1 = abstract_config_f1_1

    def bringup(self, fs):
        self.funcp_obj.bringup_funcp(prepare_docker=self.update_funcp)
        self.funcp_obj.assign_mpg_ips(static=True, f1_1_mpg=self.f1_1_mpg, f1_0_mpg=self.f1_0_mpg,
                                      f1_0_mpg_netmask="255.255.255.0",
                                      f1_1_mpg_netmask="255.255.255.0"
                                      )
        self.funcp_obj.funcp_abstract_config(abstract_config_f1_0=self.abstract_config_f1_0,
                                             abstract_config_f1_1=self.abstract_config_f1_1)


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):
        global funcp_obj, servers_list, test_bed_type
        testbed_info = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        fun_test.shared_variables['testbed_info'] = testbed_info
        fun_test.shared_variables["pcie_host_result"] = True
        # Removing any funeth driver from COMe and and all the connected server
        threads_list = []
        single_f1 = False
        if test_bed_type == 'fs-fcp-scale':
            fs_list = testbed_info['fs'][test_bed_type]["fs_list"]
            fs_index=0
        else:
            single_f1 = True
            fs_list = [test_bed_type]
            test_bed_type = 'fs-fcp-scale'
        # for fs_name in fs_list:
        #
        #     thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=clean_testbed, fs_name=fs_name,
        #                                               hu_host_list=testbed_info['fs'][test_bed_type][fs_name]
        #                                               ['hu_host_list'])
        #     threads_list.append(thread_id)
        #
        # for thread_id in threads_list:
        #     fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

        # Boot up FS1600

        topology_helper = TopologyHelper()
        for fs_name in fs_list:
            fs_name = str(fs_name)
            # FS-39 issue
            # if fs_name == "fs-39":
            #     continue
            abstract_json_file0 = \
                fun_test.get_script_parent_directory() + testbed_info['fs'][test_bed_type][fs_name][
                    'abtract_config_f1_0']
            abstract_json_file1 = \
                fun_test.get_script_parent_directory() + testbed_info['fs'][test_bed_type][fs_name][
                    'abtract_config_f1_1']
            funcp_obj = FunCPSetup(test_bed_type=fs_name,
                                   update_funcp=testbed_info['fs'][test_bed_type][fs_name]['prepare_docker'],
                                   f1_1_mpg=str(testbed_info['fs'][test_bed_type][fs_name]['mpg1']),
                                   f1_0_mpg=str(testbed_info['fs'][test_bed_type][fs_name]['mpg0']),
                                   abstract_config_f1_0=abstract_json_file0,
                                   abstract_config_f1_1=abstract_json_file1
                                   )
            index = testbed_info['fs'][test_bed_type][fs_name]['index']
            if single_f1:
                index = 0
            topology_helper.set_dut_parameters(dut_index=index,
                                               f1_parameters={0: {"boot_args": testbed_info['fs'][test_bed_type]
                                                              [fs_name]['bootargs_f1_0']},
                                                              1: {"boot_args": testbed_info['fs'][test_bed_type]
                                                              [fs_name]['bootargs_f1_1']}},
                                               fun_cp_callback=funcp_obj.bringup)

        topology = topology_helper.deploy()

        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

    def cleanup(self):
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()


class TestHostPCIeLanes(FunTestCase):
    def describe(self):
        self.set_test_details(id=1, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        pass

    def check_pcie_link_speed(self, hostname, link_speed, username="localadmin", password="Precious1*"):
        try:
            result = True
            linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
            lspci_out = linux_obj.sudo_command(command="sudo lspci -d 1dad: -vv | grep LnkSta")
            output = linux_obj.command('lspci -d 1dad:')
            link_check = re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output)
            fun_test.test_assert(expression=link_check, message="Fungible Ethernet PFs on host %s" % hostname)
            result &= bool(link_check)
            if link_speed not in lspci_out:
                if "LnkSta" not in lspci_out:
                    fun_test.test_assert(expression=False, message="PCIE link did not come up on Host %s" % hostname)
                else:
                    fun_test.test_assert(expression=False,
                                         message="PCIE link did not come up in %s mode on Host %s" % (link_speed,
                                                                                                      hostname))
                result &= False
            result &= fun_test.shared_variables["pcie_host_result"]
            fun_test.shared_variables["pcie_host_result"] = result
        except Exception as e:
            fun_test.log("==================")
            fun_test.log("Exception occurred")
            fun_test.log("==================")
            fun_test.critical(e)
            fun_test.shared_variables["pcie_host_result"] &= False

    def run(self):

        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        testbed_info = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        if test_bed_type == 'fs-fcp-scale':
            fs_list = testbed_info['fs'][test_bed_type]["fs_list"]
        else:
            fs_list = [test_bed_type]
            test_bed_type = 'fs-fcp-scale'
        threads_list = []

        for fs_name in fs_list:
            servers_mode = testbed_info['fs'][test_bed_type][fs_name]['hu_host_list']
            for server_key in servers_mode:
                for server in server_key:
                    thread_id = fun_test.execute_thread_after(time_in_seconds=1, func=self.check_pcie_link_speed,
                                                              hostname=server, link_speed=server_key[server])
                    threads_list.append(thread_id)

        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

        fun_test.test_assert(expression=fun_test.shared_variables["pcie_host_result"], message="PCIe Link Speed Check")

    def cleanup(self):
        pass


class BringupPCIeHosts(FunTestCase):
    def describe(self):
        self.set_test_details(id=2, summary="Bringup PCIe hosts",
                              steps="""
                                      1. use Funeth library and tc_config to bringup Hosts
                                      """)

    def setup(self):
        pass

    def run(self):

        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')

        tb_config_obj = tb_configs.TBConfigs(test_bed_type)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, num_queues=4)

    def cleanup(self):
        pass


class VlanPingTests(FunTestCase):
    tc_result = True

    def describe(self):
        self.set_test_details(id=3, summary="Ping from all VLANs to all others",
                              steps="""
                                      1. SSH into each F1 container
                                      """)

    def setup(self):
        pass

    def vlan_ping_test(self, source_Linux, dest_ips, fs, container):
        fail_result = []
        for f1 in dest_ips:
            dest_vlan_ip = dest_ips[f1]
            ping_result = source_Linux.ping(dst=dest_vlan_ip, count=10, max_percentage_loss=30, timeout=30, interval=0.1)
            if not ping_result:
                fail_result.append(f1)
        if fail_result == []:
            fun_test.test_assert(expression=True, message="%s %s can reach all other F1 VLANs" % (fs, container))
        else:
            fun_test.test_assert(expression=False, message="%s %s can reach all other F1 VLANs" % (fs, container))
            self.tc_result = False
        source_Linux.disconnect()

    def run(self):
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        testbed_info = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        vlan_ips = testbed_info['fs'][test_bed_type]["vlan_ips"]
        ping_threads_list = []
        for f1_docker in vlan_ips:
            fs = f1_docker.split('_')[0]
            container_name = f1_docker.split('_')[1]
            fs_spec = fun_test.get_asset_manager().get_fs_by_name(fs)
            container_obj = FunCpDockerContainer(name=container_name, host_ip=fs_spec['come']['mgmt_ip'],
                                                 ssh_username=fs_spec['come']['mgmt_ssh_username'],
                                                 ssh_password=fs_spec['come']['mgmt_ssh_password'])

            ping_thread_id = fun_test.execute_thread_after(time_in_seconds=1, func=self.vlan_ping_test,
                                                           source_Linux=container_obj, dest_ips=vlan_ips, fs=fs,
                                                           container=container_name)
            ping_threads_list.append(ping_thread_id)
            for ping_thread_id in ping_threads_list:
                fun_test.join_thread(fun_test_thread_id=ping_thread_id, sleep_time=1)

            fun_test.test_assert(expression=self.tc_result, message="All F1s can reach other F1s VLANs")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(TestHostPCIeLanes())
    test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
    if test_bed_type == 'fs-fcp-scale':
        ts.add_test_case(BringupPCIeHosts())
        ts.add_test_case(VlanPingTests())
    ts.run()
