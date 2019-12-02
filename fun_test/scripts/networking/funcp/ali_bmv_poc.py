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
vm_volume_map = {}


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                                  1. BringUP both F1s
                                  2. Bringup FunCP
                                  3. Create MPG Interfaces and assign static IPs
                                  """)

    def setup(self):
        # Last working parameter:
        # --environment={\"test_bed_type\":\"fs-alibaba_demo\",\"tftp_image_path\":\"divya_funos-f1.stripped_june5.gz\"}
        # --environment={\"test_bed_type\":\"fs-alibaba-demo\",\"tftp_image_path\":\"ysingh/funos-f1.stripped_18jun.gz\"}
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

    def cleanup(self):
        fun_test.log("Cleanup")
        # fun_test.shared_variables["topology"].cleanup()


class ScriptSetup2(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                                  1. BringUP both F1s
                                  2. Bringup FunCP
                                  3. Create MPG Interfaces and assign static IPs
                                  """)

    def setup(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        # fs_name = "fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])

    def cleanup(self):
        fun_test.log("Cleanup")
        # fun_test.shared_variables["topology"].cleanup()

class NicEmulation(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup PCIe Connceted Hosts and test traffic",
                              steps="""
                              1. Reboot connected hosts
                              2. Verify for PICe Link
                              3. Install Funeth Driver
                              4. Configure HU interface
                              5. Configure FunCP according to HU interfaces
                              6. Add routes on FunCP Container
                              7. Ping NU host from HU host
                              8. Do netperf
                              """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        # execute abstract Configs

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
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

        print("\n===========================")
        print ("Continue to NIC Emulation:")
        print("===========================")
        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
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

        tb_config_obj = tb_configs.TBConfigs(str(fs_name)+"2")
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, sriov=4, num_queues=4)

        # get ethtool output
        get_ethtool_on_hu_host(funeth_obj)
        print("\n=================")
        print ("Enable NVMe VFs:")
        print("=================")
        for server in self.server_key["fs"][fs_name]["vm_config"]:
            critical_log(enable_nvme_vfs
                         (host=server,
                          pcie_vfs_count=self.server_key["fs"][fs_name]["vm_config"][server]["pcie_vfs"]),
                         message="NVMe VFs enabled")
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host])

    def cleanup(self):
        pass


class StartVMs(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Start VMs",
                              steps="""
                              1. Create NVMe VFs
                              2. Make sure NVMe and Funeth VFs exist
                              3. Start All VMs
                              4. Configure Funeth Driver and Assign IP using Funeth VM
                              5. Make sure lspci output has both Funeth and NVMe devices
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        servers_with_vms = self.server_key["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            configure_vms(server_name=server, vm_dict=servers_with_vms[server]["vms"])

        fun_test.sleep(message="Waiting for VMs to come up", seconds=120)

    def cleanup(self):
        pass


class CreateNamespaceVMs(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=10,
                              summary="CreateNamespaceVMs",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.spec_file["fs"][fs_name]["fs-name"])


        servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            i = 1

            storage_controller = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                   target_port=42220)
            result = storage_controller.ip_cfg(ip=servers_with_vms[server]["local_controller_ip"],
                                               port=servers_with_vms[server]["local_controller_port"])

            storage_controller_remote = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                          target_port=42221)
            result = storage_controller_remote.ip_cfg(ip=servers_with_vms[server]["remote_controller_ip"],
                                                      port=servers_with_vms[server]["remote_controller_port"])
            result_dict = {}
            controller_dpu_1 = utils.generate_uuid()
            print("\n")
            print("=============================")
            print("Creating Controller on DPU 1")
            print("=============================\n")
            command_result = storage_controller_remote.create_controller(ctrlr_uuid=controller_dpu_1,
                                                                         transport="RDS",
                                                                         remote_ip=servers_with_vms[server][
                                                                          "local_controller_ip"],
                                                                         nqn="nqn-1",
                                                                         port=servers_with_vms[server][
                                                                          "local_controller_port"],
                                                                         command_duration=10)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                 format(controller_dpu_1))

            for vm in servers_with_vms[server]["vms"]:
                # if "nvme_pci_device" not in servers_with_vms[server]["vms"][vm]:
                #     continue
                # if not check_nvme_function(host=servers_with_vms[server]["vms"][vm]["hostname"],
                #                     username=servers_with_vms[server]["vms"][vm]["user"],
                #                     password=servers_with_vms[server]["vms"][vm]["password"]):
                #     fun_test.critical(message="No NVMe Function on VM %s" % vm)
                #     continue

                result_dict[vm] = {}
                blt_volume_dpu_0 = utils.generate_uuid()
                controller_dpu_0 = utils.generate_uuid()
                print("\n")
                print("=============================")
                print("Creating Controller on DPU 0")
                print("=============================\n")
                print servers_with_vms[server]["vms"][vm]["local_storage"]
                command_result = storage_controller.create_controller(ctrlr_uuid=controller_dpu_0,
                                                                      transport="PCI",
                                                                      fnid=int(servers_with_vms[server]["vms"][vm][
                                                                                   "fnid"]),
                                                                      ctlid=int(servers_with_vms[server]["ctlid"]),
                                                                      huid=int(servers_with_vms[server]["huid"]),
                                                                      command_duration=servers_with_vms[server]["vms"][
                                                                          vm]["local_storage"]["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                     format(controller_dpu_0))
                print("\n")
                print("==============================")
                print("Creating Local Volume on DPU 0")
                print("==============================\n")

                local_volume_create(storage_controller=storage_controller,
                                    vm_dict=servers_with_vms[server]["vms"][vm]["local_storage"],
                                    uuid=blt_volume_dpu_0, count=i)
                result_dict[vm]["blt_volume_dpu_0"] = blt_volume_dpu_0

                blt_volume_dpu_1 = utils.generate_uuid()

                print("\n")
                print("==============================")
                print("Creating Local Volume on DPU 1")
                print("==============================\n")
                remote_storage_config(storage_controller=storage_controller_remote,
                                      vm_dict=servers_with_vms[server]["vms"][vm]["remote_storage"],
                                      vol_uuid=blt_volume_dpu_1, count=i,
                                      ctrl_uuid=controller_dpu_1,
                                      local_ip=servers_with_vms[server]["local_controller_ip"],
                                      local_port=servers_with_vms[server]["local_controller_port"])

                fun_test.sleep(message="Sleep before F1_0 configs")
                result_dict[vm]["controller_dpu_0"] = controller_dpu_0
                result_dict[vm]["blt_volume_dpu_1"] = blt_volume_dpu_1
                result_dict[vm]["controller_dpu_1"] = controller_dpu_1

                rds_volume_dpu_0 = utils.generate_uuid()

                print("\n")
                print("===============================")
                print("Creating Remote Volume on DPU 0")
                print("===============================\n")
                rds_volume_create(storage_controller=storage_controller,
                                  vm_dict=servers_with_vms[server]["vms"][vm]["local_storage"],
                                  vol_uuid=rds_volume_dpu_0, count=i,
                                  remote_ip=servers_with_vms[server]["remote_controller_ip"],
                                  port=servers_with_vms[server]["remote_controller_port"])
                result_dict[vm]["rds_volume_dpu_0"] = rds_volume_dpu_0
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
                             .format(rds_volume_dpu_0, controller_dpu_0))
                print("\n")
                print("============================================")
                print("Attach Remote Volume to Controller  on DPU 0")
                print("============================================\n")
                result = storage_controller.attach_volume_to_controller(ctrlr_uuid=controller_dpu_0,
                                                                        vol_uuid=rds_volume_dpu_0,
                                                                        ns_id=int(i+1),
                                                                        command_duration=servers_with_vms[server][
                                                                            "vms"][vm]["local_storage"][
                                                                            "command_timeout"])
                fun_test.log(result)
                critical_log(result["status"], "Attaching volume {} to controller {}"
                             .format(rds_volume_dpu_0, controller_dpu_0))
                i += 1
            fun_test.log(result_dict)

    def cleanup(self):
        pass


class LoadFunethOnVMs(FunTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Load Funeth on all VMs",
                              steps="""
                              1. Login into each VM
                              2. show lspci output
                              3. See Funeth interface
                              4. See NVMe list output
                              5. Ping to NU host(TOR connected NU server)
                              """)

    def setup(self):
        pass

    def run(self):
        tb_config_obj = tb_configs.TBConfigs("FS-ALIBABA-DEMO-VM")
        funeth_obj = Funeth(tb_config_obj, ws='/home/localadmin/ws')
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_vm(funeth_obj, update_driver=True)

    def cleanup(self):
        pass


class LocalNamespace(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="Local/Remote read & write from VM",
                              steps="""
                              1. Login into VM
                              2. Run FIO to local volume for read/write
                              3. Run FIO to remote volume for read/write
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        global vm_volume_map
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.spec_file["fs"][fs_name]["fs-name"])

        servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            i = 1

            storage_controller = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                   target_port=42220)
            # result = storage_controller.ip_cfg(ip=servers_with_vms[server]["local_controller_ip"],
            #                                    port=servers_with_vms[server]["local_controller_port"])

            storage_controller_remote = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                          target_port=42221)
            # result = storage_controller_remote.ip_cfg(ip=servers_with_vms[server]["remote_controller_ip"],
            #                                           port=servers_with_vms[server]["remote_controller_port"])
            result_dict = {}

            for vm in servers_with_vms[server]["vms"]:
                # if "nvme_pci_device" not in servers_with_vms[server]["vms"][vm]:
                #     continue
                # if not check_nvme_function(host=servers_with_vms[server]["vms"][vm]["hostname"],
                #                     username=servers_with_vms[server]["vms"][vm]["user"],
                #                     password=servers_with_vms[server]["vms"][vm]["password"]):
                #     fun_test.critical(message="No NVMe Function on VM %s" % vm)
                #     continue

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
            vm_volume_map[server] = result_dict
            storage_controller.disconnect()

    def cleanup(self):
        pass


class CheckVMReachability(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="Make sure we can ssh into each VM",
                              steps="""
                              1. SSH into list of all VMs
                              2. Make a list of all VMs which can't be reached
                              3. Do steps 1 & 2 until all VMs are up
                              )
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        for server in self.spec_file["fs"][fs_name]["vm_config"]:
            servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"][server]["vms"]
            not_reachable_vms = []

            for vm in servers_with_vms:
                linux_obj = Linux(host_ip=servers_with_vms[vm]["hostname"], ssh_username=servers_with_vms[vm]["user"],
                                  ssh_password=servers_with_vms[vm]["password"])
                if not linux_obj.check_ssh():
                    not_reachable_vms.append(vm)
                linux_obj.disconnect()
            start_time = time.time()
            while len(not_reachable_vms) > 0:
                for vm in not_reachable_vms:
                    linux_obj = Linux(host_ip=servers_with_vms[vm]["hostname"],
                                      ssh_username=servers_with_vms[vm]["user"],
                                      ssh_password=servers_with_vms[vm]["password"])
                    if linux_obj.check_ssh():
                        fun_test.log("%s is reachable" % vm)
                        not_reachable_vms.remove(vm)
                    linux_obj.disconnect()
                if len(not_reachable_vms) > 0:
                    fun_test.sleep(message="waiting for VMs to come up", seconds=30)
                    fun_test.log("VMs not rebooted are:")
                    fun_test.log(not_reachable_vms)
                now_time = time.time()
                if int(now_time - start_time) > 1200:
                    fun_test.test_assert(expression=False, message="VMs didnt come up in 20 minutes")

    def cleanup(self):
        pass


class LoadNvmeOnVMs(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=6,
                              summary="Load NVMe on all VMs",
                              steps="""
                              1. Login into each VM
                              2. show lspci output
                              3. See Funeth interface
                              4. See NVMe list output
                              5. Ping to NU host(TOR connected NU server)
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        for server in self.spec_file["fs"][fs_name]["vm_config"]:
            servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"][server]["vms"]
            check_nvme_driver(vm_dict=servers_with_vms, parallel=True)

    def cleanup(self):
        pass


class PingTestVmVmSameServer(FunTestCase):
    spec_file = {}

    def describe(self):
        self.set_test_details(id=7,
                              summary="Load Funeth on all VMs",
                              steps="""
                              1. Login into each VM
                              2. show lspci output
                              3. See Funeth interface
                              4. See NVMe list output
                              5. Ping to NU host(TOR connected NU server)
                              """)

    def setup(self):
        self.spec_file = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                     '/fs_connected_servers.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        for server in self.spec_file["fs"][fs_name]["vm_config"]:
            servers_with_vms = self.spec_file["fs"][fs_name]["vm_config"][server]["vms"]
            same_server_pings = self.spec_file["fs"][fs_name]["vm_config"][server]["vm_ping_tests"]["vm_vm_same_server"]
            for vm in same_server_pings:
                dest_vm_ips = []
                for dest_vm in same_server_pings[vm]:
                    dest_vm_ips.append(dest_vm)
                test_host_pings(host=servers_with_vms[vm]["hostname"], strict=True, ips=dest_vm_ips)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(NicEmulation())
    # # ts.add_test_case(CreateNamespaceVMs()) // Dont use this
    ts.add_test_case(StartVMs())
    ts.add_test_case(LocalNamespace())
    ts.add_test_case(CheckVMReachability())
    # ts.add_test_case(LoadFunethOnVMs())
    # ts.add_test_case(LoadNvmeOnVMs())
    # ts.add_test_case(PingTestVmVmSameServer())
    # ts.add_test_case(PingFioTestAllVMs())
    # ts.add_test_case(TempNvmeCmds())
    # ts.add_test_case(FindVMBootTime())
    ts.run()
