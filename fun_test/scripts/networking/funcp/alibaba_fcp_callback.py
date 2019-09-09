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
import time
import datetime

CHECK_HPING3_ON_HOSTS = True


class FunCPSetup:

    def __init__(self,f1_0_mpg, f1_1_mpg, test_bed_type, abstract_config_f1_0, abstract_config_f1_1, update_funcp=True):
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

    server_key = {}
    def describe(self):
        self.set_test_details(steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):
        global funcp_obj, servers_mode, servers_list, test_bed_type
        testbed_info = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        tftp_image_path = fun_test.get_job_environment_variable('tftp_image_path')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        fun_test.shared_variables['testbed_info'] = testbed_info
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        tftp_image_path = fun_test.get_job_environment_variable('tftp_image_path')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        # Removing any funeth driver from COMe and and all the connected server
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
            funcp_obj.cleanup_funcp()
            server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
            servers_mode = server_key["fs"][fs_name]
            for server in servers_mode:
                print server
                critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
        print "\n\n\n Booting of FS started \n\n\n"
        print  datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        # Boot up FS1600
        f1_0_boot_args = testbed_info['fs'][test_bed_type]['bootargs_f1_0']
        f1_1_boot_args = testbed_info['fs'][test_bed_type]['bootargs_f1_1']
        topology_t_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        topology_helper = TopologyHelper()
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
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
            index = 0
            if fs_name == "fs-48":
                index = 0
            if fs_name == "fs-60":
                index = 1
            topology_helper.set_dut_parameters(dut_index=index,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}},
                                               fun_cp_callback=funcp_obj.bringup)

        topology = topology_helper.deploy()

        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
        print "\n\n\n Booting of FS ended \n\n\n"
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        tb_config_obj = tb_configs.TBConfigs(test_bed_type)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=True, num_queues=8)

    def cleanup(self):
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()



class TestCcCcPing(FunTestCase):
    hosts_info = {}
    host_username = "localadmin"
    host_password = "Precious1*"

    def describe(self):
        self.set_test_details(id=2, summary="Test CC --> CC Ping",
                              steps="""
                              1. Fetch all vlan ips from each docker container
                              2. Ensure all vlans can ping each other 
                              """)

    def setup(self):
        pass

    def run(self):
        test_bed_type = fun_test.shared_variables['test_bed_type']
        testbed_info = fun_test.shared_variables['testbed_info']

        checkpoint = "Ensure all vlans can ping its neighbour vlan"
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
            res = funcp_obj.test_cc_pings_fs(interval=0.01)
            fun_test.simple_assert(res, checkpoint)
        fun_test.add_checkpoint(checkpoint)

        funcp1_obj = FunControlPlaneBringup(fs_name=testbed_info['fs'][test_bed_type]["fs_list"][0])
        funcp2_obj = FunControlPlaneBringup(fs_name=testbed_info['fs'][test_bed_type]["fs_list"][1])

        funcp1_obj._get_docker_names(verify_2_dockers=False)
        funcp1_obj._get_vlan1_ips()

        funcp2_obj._get_docker_names(verify_2_dockers=False)
        funcp2_obj._get_vlan1_ips()

        checkpoint = "Ensure %s vlans can ping %s vlans" % (funcp1_obj.fs_name, funcp2_obj.fs_name)
        res = funcp1_obj.test_cc_pings_remote_fs(dest_ips=funcp2_obj.vlan1_ips.values(), from_vlan=True, interval=0.01)
        fun_test.test_assert(res, checkpoint)

        checkpoint = "Ensure %s vlans can ping %s vlans" % (funcp2_obj.fs_name, funcp1_obj.fs_name)
        res = funcp2_obj.test_cc_pings_remote_fs(dest_ips=funcp1_obj.vlan1_ips.values(), from_vlan=True, interval=0.01)
        fun_test.test_assert(res, checkpoint)

        fun_test.add_checkpoint("Ensure all vlans can ping its neighbour FS vlans")

    def cleanup(self):
        pass



class TestHostPCIeLanes(FunTestCase):
    def describe(self):
        self.set_test_details(id=6, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        pass
    def run(self):
        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            server_key = fun_test.parse_file_to_json(
                fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
            servers_mode = server_key["fs"][fs_name]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result == "1"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)


    def cleanup(self):
        pass

if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(TestCcCcPing())
    ts.add_test_case(TestHostPCIeLanes())
    ts.run()
