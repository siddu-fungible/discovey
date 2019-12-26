from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.host.storage_controller import StorageController
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
import time
from scripts.networking.funcp import ali_bmv_poc


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                                  1. BringUP both F1s
                                  2. Bringup FunCP
                                  3. Create MPG Interfaces and assign static IPs
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        # fs_name = "fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.cleanup_funcp()
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        servers_list = []

        for server in servers_mode:
            print server
            shut_all_vms(hostname=server)
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Bringup FunCP
        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        # Assign MPG IPs from dhcp
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        # funcp_obj.fetch_mpg_ips() #Only if not running the full script
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]

        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

        # Add static routes on Containers
        funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
        fun_test.sleep(message="Waiting before ping tests", seconds=10)

        # Ping QFX from both F1s
        ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        for container in ping_dict:
            funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

        # Ping vlan to vlan
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.test_cc_pings_fs()

    def cleanup(self):
        fun_test.log("Cleanup")
        # fun_test.shared_variables["topology"].cleanup()


class SetupHost(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup PCIe Connceted Hosts",
                              steps="""
                              1. Reboot connected hosts
                              2. Verify for PICe Link
                              3. Install Funeth Driver
                              4. Configure HU interface
                              5. Add NVME VFs
                              6. Add Ethernet VFs
                              """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        # execute abstract Configs

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])

        print("\n===========================")
        print ("Continue to NIC Emulation:")
        print("===========================")
        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            if server != "cab03-qa-01":
                continue
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])

        # install drivers on PCIE connected servers
        tb_config_obj = tb_configs.TBConfigs(str(fs_name))
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, sriov=32, num_queues=4)

        # get ethtool output
        get_ethtool_on_hu_host(funeth_obj)
        print("\n=================")
        print ("Enable NVMe VFs:")
        print("=================")
        for server in self.server_key["fs"][fs_name]["vm_config"]:
            if server != "cab03-qa-01":
                continue
            critical_log(enable_nvme_vfs
                         (host=server,
                          pcie_vfs_count=self.server_key["fs"][fs_name]["vm_config"][server]["pcie_vfs"]),
                         message="NVMe VFs enabled")
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            if host != "cab03-qa-01":
                continue
            test_host_pings(host=host, ips=ping_dict[host])

    def cleanup(self):
        pass


class LocalNamespace(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create PCI BLT volume for all NVMe VFs",
                              steps="""
                              1. Create 32 Volumes
                              2. Create 32 Controllers with fnid for each VF
                              3. Attach 1 volume to each controller
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.spec_file["fs"][fs_name]["fs-name"])

        servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            if server == "cab03-qa-02":
                continue

            i = 1
            storage_controller = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                   target_port=42220)
            # result = storage_controller.ip_cfg(ip=servers_with_vms[server]["local_controller_ip"],
            #                                    port=servers_with_vms[server]["local_controller_port"])

            result_dict = {}

            for vm in servers_with_vms[server]["vms"]:

                result_dict[vm] = {}
                blt_volume_dpu_0 = utils.generate_uuid()
                controller_dpu_0 = utils.generate_uuid()
                print("\n")
                print("==============================")
                print("Creating Local Volume on DPU 0")
                print("==============================\n")

                local_volume_create(storage_controller=storage_controller,
                                    vm_dict=servers_with_vms[server]["vms"][vm]["local_storage"],
                                    uuid=blt_volume_dpu_0, count=i)
                result_dict[vm] = {"blt_volume_dpu_0": blt_volume_dpu_0, "controller_dpu_0": controller_dpu_0}

                blt_volume_dpu_1 = utils.generate_uuid()

                print("\n")
                print("=============================")
                print("Creating Controller on DPU 0")
                print("=============================\n")
                print servers_with_vms[server]["vms"][vm]["local_storage"]
                command_result = storage_controller.create_controller(ctrlr_uuid=controller_dpu_0,
                                                                      transport="PCI",
                                                                      fnid=servers_with_vms[server]["vms"][vm][
                                                                                   "fnid"],
                                                                      ctlid=servers_with_vms[server]["ctlid"],
                                                                      huid=servers_with_vms[server]["huid"],
                                                                      command_duration=servers_with_vms[server]["vms"][
                                                                          vm]["local_storage"]["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                     format(controller_dpu_0))
                result_dict[vm]["controller_dpu_0"] = controller_dpu_0

                print("\n")
                print("===========================================")
                print("Attach Local Volume to Controller  on DPU 0")
                print("===========================================\n")
                result = storage_controller.attach_volume_to_controller(ctrlr_uuid=controller_dpu_0,
                                                                        vol_uuid=blt_volume_dpu_0,
                                                                        ns_id=int(i),
                                                                        command_duration=
                                                                        servers_with_vms[server]["vms"][vm][
                                                                            "local_storage"]["command_timeout"])
                fun_test.log(result)
                critical_log(result["status"], "Attaching volume {} to controller {}"
                             .format(blt_volume_dpu_0, controller_dpu_0))
                i += 1
            fun_test.log(result_dict)
            print "{:<20} | {:<18} | {:<18}".format('VM', 'Volume DPU0', 'Controller DPU0')
            for vm in result_dict:
                print "{:<20} | {:<18} | {:<18}".format(vm, result_dict[vm]['blt_volume_dpu_0'],
                                                    result_dict[vm]['controller_dpu_0'])
            storage_controller.disconnect()

    def cleanup(self):
        pass


class EthernetVFScaleTest(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="Ethernet 32 VF scale test",
                              steps="""
                              1. Assign IPs to VF interfaces
                              2. Ping from each VF interface
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        server = "cab03-qa-01"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        host = Linux(host_ip=server, ssh_username="localadmin", ssh_password="Precious1*")
        intfs = host.command("ip -o link show | awk -F': ' '{print $2}'").split()
        res = [idx for idx in intfs if idx.lower().startswith("hu")]
        res.remove("hu2-f0")
        for intf in res:
            host.command("sudo ifconfig %s 18.1.1.%s/24 up" % (intf, intf.split('f')[1]))
        result = True
        fail_list = []
        for intf in res:
            output = host.command("ping 18.1.1.1 -I 18.1.1.%s -c 5" % (intf.split('f')[1]))
            m = re.search(r'(\d+)%\s+packet\s+loss', output)
            if m:
                percentage_loss = int(m.group(1))
                if percentage_loss <= 1:
                    result &= True
                else:
                    result &= False
                    fail_list.append(intf)
        fun_test.test_assert(expression=result, message="All interface Pings | failures : %s" % str(fail_list))
        host.disconnect()

    def cleanup(self):
        pass


class NVMeVFScaleTest(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="NVMe 32 VF scale test",
                              steps="""
                              1. Check 32 nvme namespaces
                              2. FIO from each namespace
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        server = "cab03-qa-01"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        host = Linux(host_ip=server, ssh_username="localadmin", ssh_password="Precious1*")
        namespaces = host.command("lsblk -o NAME").split()
        res = [idx for idx in namespaces if idx.lower().startswith("nvme")]
        full_result = {}
        for namespace in res:
            print ("executing FIO for %s" % namespace)
            result = host.pcie_fio(filename=("/dev/%s" % namespace), runtime=30, timeout=90)
            print result
            full_result[namespace] = result
            fun_test.test_assert(expression=result, message="Fio test result for namespace %s" % namespace)
        fun_test.test_assert(expression="True", message="Find full result below")
        print full_result
        host.disconnect()

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(SetupHost())
    ts.add_test_case(LocalNamespace())
    ts.add_test_case(EthernetVFScaleTest())
    ts.add_test_case(NVMeVFScaleTest())
    ts.run()
