from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from asset.asset_manager import *
import re
import socket


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def cleanup(self):
        pass


class BringupSetup(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "f10_retimer" in job_inputs:
            f10_retimer = str(job_inputs["f10_retimer"]).strip("[]").replace(" ", "")
        else:
            f10_retimer = 0
        if "f11_retimer" in job_inputs:
            f11_retimer = str(job_inputs["f11_retimer"]).strip("[]").replace(" ", "")
        else:
            f11_retimer = 0
        if "f10_boot_huid" in job_inputs:
            f10_boot_huid = str(job_inputs["f10_boot_huid"]).strip("[]").replace(" ", "")
        else:
            f10_boot_huid = 2
        if "f11_boot_huid" in job_inputs:
            f11_boot_huid = str(job_inputs["f11_boot_huid"]).strip("[]").replace(" ", "")
        else:
            f11_boot_huid = 1
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} nvme_boot_huids={} --mgmt".format(f10_retimer, f10_boot_huid)
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} nvme_boot_huids={} --mgmt".format(f11_retimer, f11_boot_huid)

        topology_helper = TopologyHelper()

        fun_test.shared_variables["enable_fcp"] = False

        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        if "total_blt" in job_inputs:
            total_blt = job_inputs["total_blt"]
            fun_test.shared_variables["total_blt"] = total_blt
        else:
            fun_test.shared_variables["total_blt"] = 1
        if "deploy_vol" in job_inputs:
            deploy_vol = job_inputs["deploy_vol"]
            fun_test.shared_variables["deploy_vol"] = deploy_vol
            if not deploy_vol:
                f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer={} nvme_boot_huids={} --mgmt".format(f10_retimer, f10_boot_huid)
                f1_1_boot_args = "app=load_mods cc_huid=2 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer={} nvme_boot_huids={} --mgmt".format(f11_retimer, f11_boot_huid)
                fun_test.log_section("Volumes are not being deployed, using boot args :")
                print f1_0_boot_args
                print f1_1_boot_args
        else:
            fun_test.shared_variables["deploy_vol"] = True
            fun_test.log_section("Booting using args :")
            print f1_0_boot_args
            print f1_1_boot_args

        # Get the HUID's for nvme_boot for F1_0 used during attach of RDS vol to PCIe controller
        fun_test.shared_variables["f10_huid"] = job_inputs["boot_huid"]

        if deploy_setup:
            funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
            funcp_obj.cleanup_funcp()
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            servers_list = []

            for server in servers_mode:
                critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
                servers_list.append(server)

            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}}
                                               )
            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")
            fs = topology.get_dut_instance(index=0)
            come_obj = fs.get_come()
            fun_test.shared_variables["come_obj"] = come_obj
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("iptables -F")
            come_obj.sudo_command("ip6tables -F")
            come_obj.sudo_command("dmesg -c > /dev/null")

            fun_test.log("Getting host details")
            host_dict = {"f1_0": [], "f1_1": []}
            for i in range(0, 23):
                if i <= 11:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_0"]:
                            host_dict["f1_0"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
                elif i > 11 <= 23:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_1"]:
                            host_dict["f1_1"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
            fun_test.shared_variables["hosts_obj"] = host_dict

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")

            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])
        else:
            # Get COMe object
            am = AssetManager()
            th = TopologyHelper(spec=am.get_test_bed_spec(name=fs_name))
            topology = th.get_expanded_topology()
            dut = topology.get_dut(index=0)
            dut_name = dut.get_name()
            fs_spec = fun_test.get_asset_manager().get_fs_by_name(name=dut_name)
            fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True)
            come_obj = fs_obj.get_come()
            fun_test.shared_variables["come_obj"] = come_obj

            fun_test.log("Getting host info")
            host_dict = {"f1_0": [], "f1_1": []}
            temp_host_list = []
            temp_host_list1 = []
            expanded_topology = topology_helper.get_expanded_topology()
            pcie_hosts = expanded_topology.get_pcie_hosts_on_interfaces(dut_index=0)
            for pcie_interface_index, host_info in pcie_hosts.iteritems():
                host_instance = fun_test.get_asset_manager().get_linux_host(host_info["name"])
                if pcie_interface_index <= 11:
                    if host_info["name"] not in temp_host_list:
                        host_dict["f1_0"].append(host_instance)
                        temp_host_list.append(host_info["name"])
                elif pcie_interface_index > 11 <= 23:
                    if host_info["name"] not in temp_host_list1:
                        host_dict["f1_1"].append(host_instance)
                        temp_host_list1.append(host_info["name"])
            fun_test.shared_variables["hosts_obj"] = host_dict

        fun_test.shared_variables["host_len_f10"] = len(host_dict["f1_0"])
        fun_test.shared_variables["host_len_f11"] = len(host_dict["f1_1"])

        fun_test.log("SETUP Done")

    def cleanup(self):
        pass


class NicEmulation(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup PCIe Connected Hosts and test traffic",
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
        host_objs = fun_test.shared_variables["hosts_obj"]
        enable_fcp = fun_test.shared_variables["enable_fcp"]
        come_obj = fun_test.shared_variables["come_obj"]
        abstract_key = ""
        if enable_fcp:
            abstract_key = "abstract_configs_bgp"
        else:
            abstract_key = "abstract_configs"

        if fun_test.shared_variables["deploy_setup"]:
            fun_test.log("Using abstract_key {}".format(abstract_key))
            # execute abstract Configs
            abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name][abstract_key]["F1-0"]
            abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name][abstract_key]["F1-1"]

            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

            if not enable_fcp:
                # Add static routes on Containers
                funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])

            fun_test.sleep(message="Waiting before ping tests", seconds=10)

            # Ping QFX from both F1s
            ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
            if enable_fcp:
                ping_dict = self.server_key["fs"][fs_name]["cc_pings_bgp"]

            for container in ping_dict:
                funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

            # Ping vlan to vlan
            funcp_obj.test_cc_pings_fs()

            # Print the tunnel info if its FCP
            if enable_fcp:
                come_obj.sudo_command("echo SELECT 1 > /scratch/opt/fungible/f10_tunnel")
                come_obj.sudo_command("echo keys *fcp* >> /scratch/opt/fungible/f10_tunnel")
                come_obj.sudo_command("echo SELECT 1 > /scratch/opt/fungible/f11_tunnel")
                come_obj.sudo_command("echo keys *fcp* >> /scratch/opt/fungible/f11_tunnel")
                fun_test.log_section("F1_0 Tunnel Info")
                come_obj.command("docker exec F1-0 bash -c \"redis-cli < f10_tunnel\"")
                fun_test.log_section("F1_1 Tunnel Info")
                come_obj.command("docker exec F1-1 bash -c \"redis-cli < f11_tunnel\"")
                fun_test.sleep("FCP config done", 15)

        # Create a dict containing F1_0 & F1_1 details
        # TODO, check to see if the interface name is returned or not.
        f10_hosts = []
        f11_hosts = []
        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("dmesg -c > /dev/null")
                hostname = handle.command("hostname").strip()
                iface_name = handle.command(
                    "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | head -1 | tr -d :"). \
                    strip()
                iface_addr = handle.command(
                    "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(
                        iface_name)).strip()
                if objs == "f1_0":
                    f10_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                     "handle": handle}
                    f10_hosts.append(f10_host_dict)
                elif objs == "f1_1":
                    f11_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                     "handle": handle}
                    f11_hosts.append(f11_host_dict)
        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts

        fun_test.sleep("Setup deployed, starting storage config", 10)

    def cleanup(self):
        pass


class ConfigureRdsVol(FunTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Configure RDS vol",
                              steps="""                              
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]
        come_obj = fun_test.shared_variables["come_obj"]
        deploy_vol = fun_test.shared_variables["deploy_vol"]
        f10_huid = fun_test.shared_variables["f10_huid"]

        command_timeout = 5
        f10_vlan_ip = \
            come_obj.command("docker exec -it F1-0 \"\"ifconfig vlan1 | grep -e 'inet ' | awk -F ' ' '{print $2}'\"\"")
        f10_vlan_ip = f10_vlan_ip.strip()
        f11_vlan_ip = \
            come_obj.command("docker exec -it F1-1 \"\"ifconfig vlan1 | grep -e 'inet ' | awk -F ' ' '{print $2}'\"\"")
        f11_vlan_ip = f11_vlan_ip.strip()
        drive_size = 32212254720
        total_blt = fun_test.shared_variables["total_blt"]

        # Storage Controller Objects
        f10_storage_ctrl_obj = StorageController(target_ip=come_obj.host_ip, target_port=40220)
        f11_storage_ctrl_obj = StorageController(target_ip=come_obj.host_ip, target_port=40221)

        # Create IPCFG on F1_0
        command_result = f10_storage_ctrl_obj.ip_cfg(ip=f10_vlan_ip, port=4420)
        fun_test.test_assert(command_result["status"], "ip_cfg on F1_0 COMe")

        # Create IPCFG on F1_1
        command_result = f11_storage_ctrl_obj.ip_cfg(ip=f11_vlan_ip, port=4420)
        fun_test.test_assert(command_result["status"], "ip_cfg on F1_1 COMe")

        # Get list of drives on F1_1
        drive_dict = f11_storage_ctrl_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                               command_duration=command_timeout)
        drive_uuid_list = sorted(drive_dict["data"].keys())

        if deploy_vol:
            # Create a PCIe controller on F11
            f11_pcie_ctrl = utils.generate_uuid()
            command_result = f11_storage_ctrl_obj.create_controller(ctrlr_uuid=f11_pcie_ctrl,
                                                                    transport="PCI",
                                                                    fnid=2,
                                                                    ctlid=0,
                                                                    huid=1,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"],
                                   "Creation of PCI controller with uuid {} on F11".format(f11_pcie_ctrl))

            blt_uuid = {}
            nsid = 0
            for blt_count in xrange(0, total_blt):
                # Create BLT on F1_1 & attach it to PCIe
                blt_uuid[blt_count] = utils.generate_uuid()
                blt_name = "blt_" + str(blt_count)
                command_result = f11_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                    capacity=drive_size,
                                                                    block_size=4096,
                                                                    name=blt_name,
                                                                    uuid=blt_uuid[blt_count],
                                                                    drive_uuid=drive_uuid_list[blt_count].strip(),
                                                                    command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "Creation of BLT with uuid {} on F11".
                                       format(blt_uuid[blt_count]))
                fun_test.sleep("Created BLT on F11", 2)

                # Attach Volume to PCIe controller
                nsid = 1 + blt_count
                command_result = f11_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=blt_uuid[blt_count],
                                                                                  ctrlr_uuid=f11_pcie_ctrl,
                                                                                  ns_id=nsid,
                                                                                  command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "Attaching BLT {} vol to F11 PCIe controller".
                                       format(blt_uuid[blt_count]))
                fun_test.sleep("Attaching BLT vol to F11 PCIe controller", 2)

            # Install OS from image
            # fetch_devices = fetch_nvme_device(end_host=f11_hosts[0]["handle"])

            fun_test.log("Created {} BLT and attached it to PCIe controller".format(total_blt))
            nsid = 0
            for blt_count in xrange(0, total_blt):
                nsid = 1 + blt_count
                command_result = f11_storage_ctrl_obj.detach_volume_from_controller(ctrlr_uuid=f11_pcie_ctrl,
                                                                                    ns_id=nsid,
                                                                                    command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "Detached volume from PCIe controller")
                fun_test.sleep("Detached F11 BLT from PCIe controller", 10)

            command_result = f11_storage_ctrl_obj.delete_controller(ctrlr_uuid=f11_pcie_ctrl,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "Deleted PCIe controller")

        if not deploy_vol:
            fun_test.log("Volumes not deployed...")
            drive_dict = f11_storage_ctrl_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN",
                                                   command_duration=command_timeout)
            blt_uuid = {}
            count = 0
            for key in drive_dict["data"]:
                if key != "drives":
                    blt_uuid[count] = key
                    count += 1

        # Create RDS controller on F11
        f11_rds_ctrl = utils.generate_uuid()
        command_result = f11_storage_ctrl_obj.create_controller(ctrlr_uuid=f11_rds_ctrl,
                                                                transport="RDS",
                                                                nqn="nqn1",
                                                                port=4420,
                                                                remote_ip=f10_vlan_ip,
                                                                command_duration=command_timeout)
        fun_test.simple_assert(command_result["status"],
                               "F1_1 : Creation of RDS controller with uuid {}".format(f11_rds_ctrl))
        fun_test.sleep("Created RDS Controller on F11", 2)
        nsid = 0
        f10_rds_vol = {}
        f10_pcie_ctrl = {}
        for blt_count in xrange(0, total_blt):
            nsid = 1 + blt_count

            # Attach the RDS controller to BLT volume
            command_result = f11_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=blt_uuid[blt_count],
                                                                              ctrlr_uuid=f11_rds_ctrl,
                                                                              ns_id=nsid,
                                                                              command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_1 : Attach BLT to RDS controller ")
            fun_test.sleep("Attach BLT to F11 RDS controller", 2)

            # Create RDS volume on F1_0
            f10_rds_vol[blt_count] = utils.generate_uuid()
            command_result = f10_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                capacity=drive_size,
                                                                block_size=4096,
                                                                name="rds_vol" + str(nsid),
                                                                uuid=f10_rds_vol[blt_count],
                                                                remote_nsid=nsid,
                                                                remote_ip=f11_vlan_ip,
                                                                port=4420,
                                                                command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_0 : Created RDS volume")
            fun_test.sleep("Created RDS Volume on F1_0", 5)

            # Create PCIe controller
            f10_pcie_ctrl[blt_count] = utils.generate_uuid()
            command_result = f10_storage_ctrl_obj.create_controller(transport="PCI",
                                                                    ctrlr_uuid=f10_pcie_ctrl[blt_count],
                                                                    ctlid=0,
                                                                    huid=f10_huid[blt_count],
                                                                    fnid=2,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_0 : Create PCIe controller")
            fun_test.sleep("Created PCIe controller on F1_0", 5)

            # Attach PCIe controller to host
            command_result = f10_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=f10_rds_vol[blt_count],
                                                                              ctrlr_uuid=f10_pcie_ctrl[blt_count],
                                                                              ns_id=nsid,
                                                                              command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_0 : Attach PCIe controller to RDS volume")
            fun_test.sleep("Attach volume to PCIe controller on F1_0", 5)

        f10_storage_ctrl_obj.disconnect()
        f11_storage_ctrl_obj.disconnect()

        fun_test.log("Config done")

    def cleanup(self):
        pass


class RunFioRds(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Run fio traffic from host",
                              steps="""
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]
        come_obj = fun_test.shared_variables["come_obj"]
        command_timeout = 5

        fetch_nvme = fetch_nvme_device(end_host=f11_hosts[0]["handle"], nsid=1)
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
        self.nvme_block_device = fetch_nvme['nvme_device']
        fun_test.shared_variables["nvme_block_device"] = fetch_nvme['nvme_device']

        fio_seq_tests = ["write", "read"]
        for test in fio_seq_tests:
            fio_result = f11_hosts[0]["handle"].pcie_fio(filename=self.nvme_block_device,
                                                         bs="4k",
                                                         numjobs=1,
                                                         iodepth=16,
                                                         direct=1,
                                                         rw=test,
                                                         runtime=60,
                                                         verify="pattern",
                                                         verify_pattern="\\\"DEADCAFE\\\"",
                                                         timeout=120)
            fun_test.simple_assert(fio_result, message="FIO {} test".format(test))

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(ConfigureRdsVol())
    # ts.add_test_case(RunFioRds())
    ts.run()
