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

class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        pass

    def cleanup(self):
        pass


class BringupSetup(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FCP Setup",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):

        pass

    def run(self):
        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fcp_bgp_alone.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        tftp_image_path = fun_test.get_job_environment_variable('tftp_image_path')
        fun_test.shared_variables["test_bed_type"] = test_bed_type

        # Removing any funeth driver from COMe and and all the connected server
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
            funcp_obj.cleanup_funcp()

        print "\n\n\n Booting of FS started \n\n\n"
        print  datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') 
        
        # Boot up FS1600
        f1_0_boot_args = testbed_info['fs'][test_bed_type]['bootargs_f1_0']
        f1_1_boot_args = testbed_info['fs'][test_bed_type]['bootargs_f1_1']
        topology_t_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                         1: {"boot_args": f1_1_boot_args}}
                                          )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
        print "\n\n\n Booting of FS ended \n\n\n"
        print  datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            funcp_obj = FunControlPlaneBringup(fs_name=fs_name)

            print "\n\n\n Booting of Control Plane  Started\n\n\n"
            print  datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(
                prepare_docker=testbed_info['fs'][test_bed_type][fs_name]['prepare_docker']), message="Bringup FunCP")
            print "\n\n\n Booting of Control Plane  ended\n\n\n"
            print  datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=True, f1_1_mpg=str(testbed_info['fs'][test_bed_type][fs_name]['mpg1']), f1_1_mpg_netmask=str(testbed_info['fs'][test_bed_type][fs_name]['mpg1_netmask']),
                                     f1_0_mpg=str(testbed_info['fs'][test_bed_type][fs_name]['mpg0']), f1_0_mpg_netmask=str(testbed_info['fs'][test_bed_type][fs_name]['mpg0_netmask']))
            #funcp_obj.assign_mpg_ips(static=False)
            #funcp_obj.fetch_mpg_ips() #Only if not running the full script
            #execute abstract file

            abstract_json_file0 = \
                fun_test.get_script_parent_directory() + testbed_info['fs'][test_bed_type][fs_name]['abtract_config_f1_0']
            abstract_json_file1 = \
                fun_test.get_script_parent_directory() + testbed_info['fs'][test_bed_type][fs_name]['abtract_config_f1_1']
            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1, workspace="/scratch")
         
    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    # ts.add_test_case(SetupVMs)
    ts.run()
