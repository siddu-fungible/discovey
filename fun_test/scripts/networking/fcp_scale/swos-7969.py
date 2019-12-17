import sys
import os
#sys.path.append('/workspace/Integration/fun_test')
#/usr/bin/python
from lib.system.fun_test import *
from lib.host.linux import Linux
from StringIO import StringIO
import random
from lib.system.fun_test import *
from lib.system import utils
from lib.fun.fs import Fs
from lib.fun.fs import Bmc

import re
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from lib.topology.topology_helper import TopologyHelper
import ipaddress
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform

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
        fun_test.shared_variables["host_ping_result"] = True

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))

        if "controller_f1" in job_inputs:
            fun_test.shared_variables["controller_f1"] = job_inputs["controller_f1"]
        else:
            fun_test.shared_variables["controller_f1"] = "f10"



        if "host" in job_inputs:
            fun_test.shared_variables["host"] = job_inputs["host"]
        else:
            fun_test.shared_variables["host"] = "mpoc-server06"

        if "host_intf" in job_inputs:
            fun_test.shared_variables["host_intf"] = job_inputs["host_intf"]
        else:
            fun_test.shared_variables["host_intf"] = "enp216s0"

        if "enable_fcp_rds" in job_inputs:
            enable_fcp_rds = job_inputs["enable_fcp_rds"]
            fun_test.shared_variables["enable_fcp_rds"] = enable_fcp_rds
        else:
            enable_fcp_rds = False
            fun_test.shared_variables["enable_fcp_rds"] = enable_fcp_rds

        # Removing any funeth driver from COMe and and all the connected server
        threads_list = []
        single_f1 = False

        if test_bed_type == 'fs-fcp-scale' or test_bed_type == 'fs-fcp-scale-networking':
            fs_list = testbed_info['fs'][test_bed_type]["fs_list"]
            fs_index = 0
        else:
            single_f1 = True
            fs_list = [test_bed_type]
            test_bed_type = 'fs-fcp-scale'

        # Reboot host
        host1 = fun_test.shared_variables["host"]
        fun_test.log("Rebooting host: {}".format(host1))
        host1_handle = Linux(host_ip=host1, ssh_username="localadmin", ssh_password="Precious1*")
        if 1:
            host1_handle.reboot(non_blocking=True)
            host1_handle.disconnect()

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
            f10_bootarg = testbed_info['fs'][test_bed_type][fs_name]['bootargs_f1_0']
            f11_bootarg = testbed_info['fs'][test_bed_type][fs_name]['bootargs_f1_1']
            if enable_fcp_rds:
                f10_bootarg += " rdstype=fcp"
                f11_bootarg += " rdstype=fcp"
            topology_helper.set_dut_parameters(dut_index=index,
                                               f1_parameters={0: {"boot_args": f10_bootarg},
                                                              1: {"boot_args": f11_bootarg}},
                                               fun_cp_callback=funcp_obj.bringup)
        print "Reached here"
        topology = topology_helper.deploy()

        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Ensure all hosts are up after reboot
        fun_test.test_assert(host1_handle.ensure_host_is_up(max_wait_time=240),
                             message="Ensure Host {} is reachable after reboot".format(host1))

        # Ensure required modules are loaded on host server, if not load it
        for module in ['nvme', 'nvme_tcp', 'nvmet']:
            module_check = host1_handle.lsmod(module)
            if not module_check:
                host1_handle.modprobe(module)
                module_check = host1_handle.lsmod(module)
                fun_test.sleep("Loading {} module".format(module))
            fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        fs = fun_test.shared_variables["test_bed_type"]

        fs_bmc = fs.replace("-", "") + "-bmc"
        bmc_username = "sysadmin"
        bmc_passwd = "superuser"

        bmc_handle = Bmc(host_ip=fs_bmc,
                         ssh_username=bmc_username,
                         ssh_password=bmc_passwd,
                         set_term_settings=True,
                         disable_uart_logger=False)
        bmc_handle.start_uart_log_listener(f1_index=0,serial_device='/dev/ttyS0')
        bmc_handle.start_uart_log_listener(f1_index=1,serial_device='/dev/ttyS2')

        fun_test.shared_variables["bmc_handle"] = bmc_handle

    def cleanup(self):
        # Remove uart log files
        bmc_handle = fun_test.shared_variables["bmc_handle"]
        for index in [0,1]:
            bmc_handle.remove_file(bmc_handle.get_f1_uart_log_file_name(index))


        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()

class SWOS_7929(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Repro steps for SWOS-7929",
                              steps='''''')

    def setup(self):

        pass

    def run(self):

        fs = fun_test.shared_variables["test_bed_type"]
        f1 = fun_test.shared_variables["controller_f1"]
        host = fun_test.shared_variables["host"]
        host_intf = fun_test.shared_variables["host_intf"]
        bmc_handle = fun_test.shared_variables["bmc_handle"]

        print "FS is %s , f1 is %s, host is %s, host_intf is %s" %(fs,f1,host,host_intf)
        num_vols = 2
        ipconfig = 1
        ipcfg_port = 1099
        command_timeout = 5
        blt_capacity = 107374182400
        blt_blk_size = 4096
        fabric_transport = "tcp"
        nvme_io_queues = 16


        # Connect to FS-come
        fs_come = fs.replace("-", "") + "-come"
        fs_come_handle = Linux(host_ip=fs_come, ssh_username="fun", ssh_password="123")
        if f1 == 'f10':
            f1_handle = StorageController(target_ip=fs_come, target_port=42220)
            docker = 'F1-0'
            f1_index = 0
        else:
            f1_handle = StorageController(target_ip=fs_come, target_port=42221)
            docker = 'F1-1'
            f1_index = 1
        f1_loopback_ip = fs_come_handle.command("docker exec -it %s ifconfig vlan1 | "
                                                                      "grep -e 'inet ' | awk -F ' ' '{print $2}'" %(docker))
        f1_loopback_ip = f1_loopback_ip.strip()
        ipaddress.ip_address(unicode(f1_loopback_ip))

        params = {
            'drives' : [],
            'volumes' : {
                'device': [],
                'uuid' : [],
            },
            'controllers': {
                'nqn' : [],
                'uuid':  [],
            },
            'host_ips' : [],
            'nsid' : {}
        }

        # Connect to the host
        host_handle = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
        host_ip = host_handle.command(
                        "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(
                            host_intf)).strip()

        params['host_ips'].append(host_ip)
        # Create storage listener

        if ipconfig:
            command_result = f1_handle.ip_cfg(ip=f1_loopback_ip, port=ipcfg_port)
            fun_test.simple_assert(command_result["status"], "IPCFG on F1")

        # Get drive info
        drive_dict = f1_handle.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                             command_duration=command_timeout)
        params['drives'] = sorted(drive_dict["data"].keys())

        # Create 2 BLT volumes
        for x in range(0,num_vols):
            vol_id = utils.generate_uuid()
            drive = params['drives'][x]
            vol_name = 'blt' + str(x)
            params['volumes']['uuid'].append(vol_id)
            params['volumes']['device'].append(params['drives'][x])

            command_result = f1_handle.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                              capacity=blt_capacity,
                                                                              block_size=blt_blk_size,
                                                                              name=vol_name,
                                                                              uuid=vol_id,
                                                                              drive_uuid=drive,
                                                                              command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F1".format(x))


        # Create 1 NVME/TCP controller
        ctrl_uuid = utils.generate_uuid()
        nqn_name = 'nqn01'
        params['controllers']['uuid'].append(ctrl_uuid)
        params['controllers']['nqn'].append(nqn_name)
        command_result = f1_handle.create_controller(
            ctrlr_uuid=ctrl_uuid,
            transport=fabric_transport.upper(),
            remote_ip=params['host_ips'][0],
            port=ipcfg_port,
            nqn=nqn_name,
            command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "F1 Create of fabric controller {} to remote {}".
                             format(str(nqn_name), params['host_ips'][0]))

        # Attach the first volume to the NVME/TCP controller
        ns_id = 9
        command_result = f1_handle.attach_volume_to_controller(
            ctrlr_uuid=params['controllers']['uuid'][0],
            ns_id=ns_id,
            vol_uuid=params['volumes']['uuid'][0],
            command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Attach vol_{}".format(str(ns_id)))

        # Do nvme connect from the host
        # NMVe connect from x86 server to FS
        host_handle.modprobe("nvme_tcp")
        check_nvmetcp = host_handle.lsmod("nvme_tcp")
        fun_test.sleep("Waiting for load to complete", 2)
        if not check_nvmetcp:
            fun_test.critical("nvme_tcp load failed on host")

        host_handle.sudo_command("nvme connect -t {} -n {} -a {} -q {} -i {} -s {}".
                                                format(fabric_transport.lower(),
                                                       params['controllers']['nqn'][0],
                                                       f1_loopback_ip,
                                                       host_ip,
                                                       nvme_io_queues,
                                                       ipcfg_port),
                                                timeout=90)

        # Attach the second volume to the first controller
        ns_id = 10
        command_result = f1_handle.attach_volume_to_controller(
            ctrlr_uuid=params['controllers']['uuid'][0],
            ns_id=ns_id,
            vol_uuid=params['volumes']['uuid'][1],
            command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Attach vol_{}".format(str(ns_id)))

        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.read_file(uart_log_file)
        print "Log file contents " + str(log_file_contents)
        if "Unsupported log page 4" in log_file_contents:
            nvme_error = 0
        else:
            nvme_error = 1

        fun_test.test_assert(nvme_error, "Unsupported log page 4")




    def cleanup(self):
        pass

if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(SWOS_7929())
    ts.run()



