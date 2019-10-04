from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from asset.asset_manager import *
import re
import ipaddress


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def cleanup(self):
        # host_obj = fun_test.shared_variables["hosts_obj"]

        # Check if funeth is loaded or else bail out
        # for obj in host_obj:
        #     host_obj[obj][0].sudo_command("rmmod funrdma")
        # fun_test.log("Unload funrdma drivers")
        pass
        # funcp_obj.cleanup_funcp()
        # for server in servers_mode:
        #     critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")


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
        # Last working parameter:
        # --environment={\"test_bed_type\":\"fs-alibaba_demo\",\"tftp_image_path\":\"divya_funos-f1.stripped_june5.gz\"}

        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=3 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=3 workload=storage"

        # module_log=tcp:DEBUG,fabrics_host:INFO,rdsvol:INFO
        topology_helper = TopologyHelper()
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        if "deploy_vol" in job_inputs:
            deploy_vol = job_inputs["deploy_vol"]
            fun_test.shared_variables["deploy_vol"] = deploy_vol
        else:
            fun_test.shared_variables["deploy_vol"] = True
        if "enable_fcp" in job_inputs:
            enable_fcp = job_inputs["enable_fcp"]
            fun_test.shared_variables["enable_fcp"] = enable_fcp
            if enable_fcp:
                f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer=0 rdstype=fcp --mgmt --disable-wu-watchdog syslog=3 workload=storage"
                f1_1_boot_args = "app=load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer=0 rdstype=fcp --mgmt --disable-wu-watchdog syslog=3 " \
                                 "workload=storage"
        else:
            fun_test.shared_variables["enable_fcp"] = False
        if "total_ssd" in job_inputs:
            total_ssd = job_inputs["total_ssd"]
            fun_test.shared_variables["total_ssd"] = total_ssd
        else:
            fun_test.shared_variables["total_ssd"] = 1
        if "wp_policy_debug" in job_inputs:
            wp_policy_debug = job_inputs["wp_policy_debug"]
            if wp_policy_debug:
                f1_0_boot_args = f1_0_boot_args + " --wp-policy-debug"
                f1_1_boot_args = f1_1_boot_args + " --wp-policy-debug"
        if "collect_artifacts" in job_inputs:
            collect_artifacts = job_inputs["collect_artifacts"]
            fun_test.shared_variables["collect_artifacts"] = collect_artifacts
        else:
            fun_test.shared_variables["collect_artifacts"] = True
        if "skip_ctrlr_creation" in job_inputs:
            skip_ctrlr_creation = job_inputs["skip_ctrlr_creation"]
            fun_test.shared_variables["skip_ctrlr_creation"] = skip_ctrlr_creation
        else:
            fun_test.shared_variables["skip_ctrlr_creation"] = False
        if "encryption" in job_inputs:
            encryption = job_inputs["encryption"]
            fun_test.shared_variables["encryption"] = encryption
        else:
            fun_test.shared_variables["encryption"] = False

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
            print "******** ******** ******** ******** ******** ******** ******** ******** ******** "
            print "Manu, you are using a workaround in funcp_config.py line 201 to prevent timeout"
            print "******** ******** ******** ******** ******** ******** ******** ******** ******** "
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
                f10_ftep_status = come_obj.command("docker exec F1-0 bash -c \"redis-cli < f10_tunnel\"")
                fun_test.log_section("F1_1 Tunnel Info")
                f11_ftep_status = come_obj.command("docker exec F1-1 bash -c \"redis-cli < f11_tunnel\"")
                fun_test.sleep("FCP Configured", 120)

                if "openconfig-fcp:fcp-tunnel[ftep='4.4.4.4'][tunnel-type='0']" in f10_ftep_status:
                    print "********** BGP is up **********"
                    print f10_ftep_status
                if "openconfig-fcp:fcp-tunnel[ftep='3.3.3.3'][tunnel-type='0']" in f11_ftep_status:
                    print f11_ftep_status

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []
        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("dmesg -c > /dev/null")
                hostname = handle.command("hostname").strip()

                if handle.lsmod("funeth"):
                    iface_name = handle.command(
                        "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | "
                        "head -1 | tr -d :").strip()
                    iface_addr = handle.command(
                        "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".
                            format(iface_name)).strip()
                    if objs == "f1_0":
                        f10_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                         "handle": handle}
                        f10_hosts.append(f10_host_dict)
                    elif objs == "f1_1":
                        f11_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                         "handle": handle}
                        f11_hosts.append(f11_host_dict)
                else:
                    if objs == "f1_0":
                        f10_host_dict = {"name": hostname, "handle": handle}
                        f10_hosts.append(f10_host_dict)
                    elif objs == "f1_1":
                        f11_host_dict = {"name": hostname, "handle": handle}
                        f11_hosts.append(f11_host_dict)

        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts

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
        skip_ctrlr_creation = fun_test.shared_variables["skip_ctrlr_creation"]
        total_ssd = fun_test.shared_variables["total_ssd"]
        encryption = fun_test.shared_variables["encryption"]
        drive_size = 21474836480
        command_timeout = 5

        # Fetch the VLAN IP on F10 & F11 containers
        f10_vlan_ip = \
            come_obj.command("docker exec -it F1-0 \"\"ifconfig vlan1 | grep -e 'inet ' | awk -F ' ' '{print $2}'\"\"")
        f10_vlan_ip = f10_vlan_ip.strip()
        try:
            ip = ipaddress.ip_address(unicode(f10_vlan_ip))
        except ValueError:
            fun_test.log("F10 vlan IP {} is not valid".format(ip))
            fun_test.simple_assert(False, "F10 vlan IP is in wrong format")
        f11_vlan_ip = \
            come_obj.command("docker exec -it F1-1 \"\"ifconfig vlan1 | grep -e 'inet ' | awk -F ' ' '{print $2}'\"\"")
        f11_vlan_ip = f11_vlan_ip.strip()

        try:
            ip = ipaddress.ip_address(unicode(f11_vlan_ip))
        except ValueError:
            fun_test.log("F11 vlan IP {} is not valid".format(ip))
            fun_test.simple_assert(False, "F11 vlan IP is in wrong format")

        # Stop udev services on host
        service_list = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in service_list:
            for f10_obj in f10_hosts:
                service_status = f10_obj["handle"].systemctl(service_name=service, action="stop")
                fun_test.simple_assert(service_status, "Stopping {} service on {}".format(service, f10_obj["name"]))

            for f11_obj in f11_hosts:
                service_status = f11_obj["handle"].systemctl(service_name=service, action="stop")
                fun_test.simple_assert(service_status, "Stopping {} service on {}".format(service, f11_obj["name"]))

        # Storage Controller Objects
        f10_storage_ctrl_obj = StorageController(target_ip=come_obj.host_ip, target_port=40220)
        f11_storage_ctrl_obj = StorageController(target_ip=come_obj.host_ip, target_port=40221)
        fun_test.shared_variables["f10_storage_ctrl_obj"] = f10_storage_ctrl_obj
        fun_test.shared_variables["f11_storage_ctrl_obj"] = f11_storage_ctrl_obj

        if not skip_ctrlr_creation:
            # Create IPCFG on F1_0
            command_result = f10_storage_ctrl_obj.ip_cfg(ip=f10_vlan_ip, port=4420)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_0 COMe")

            # Create IPCFG on F1_1
            command_result = f11_storage_ctrl_obj.ip_cfg(ip=f11_vlan_ip, port=4420)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_1 COMe")

            # Get list of drives on F1_1
            drive_dict = f10_storage_ctrl_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                   command_duration=command_timeout)
            drive_uuid_list = sorted(drive_dict["data"].keys())
            f10_drive_count = len(drive_uuid_list)

            if total_ssd > len(drive_uuid_list):
                fun_test.test_assert_expected(False, "SSD count on FS: {} lesser than requirement : {}".
                                              format(total_ssd, f10_drive_count))

            # Create RDS controller on F1_0
            f10_rds_ctrl = utils.generate_uuid()
            command_result = f10_storage_ctrl_obj.create_controller(ctrlr_uuid=f10_rds_ctrl,
                                                                    transport="RDS",
                                                                    nqn="nqn1",
                                                                    port=4420,
                                                                    remote_ip=f11_vlan_ip,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"],
                                   "F1_0 : Creation of RDS controller with uuid {}".format(f10_rds_ctrl))

        if deploy_vol:
            drive_index = 0
            f11_rds_vol = {}
            blt_uuid = {}
            for x in xrange(1, total_ssd + 1):
                # Create BLT on F1_0 on each SSD & attach it to RDS controller
                blt_name = "thin_blt_" + str(x)
                blt_uuid[x] = utils.generate_uuid()
                if encryption:
                    xts_key = utils.generate_key(32)
                    xts_tweak = utils.generate_key(8)
                    command_result = f10_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                        capacity=drive_size,
                                                                        block_size=4096,
                                                                        name=blt_name,
                                                                        uuid=blt_uuid[x],
                                                                        drive_uuid=drive_uuid_list[drive_index].strip(),
                                                                        encrypt=True,
                                                                        key=xts_key,
                                                                        xtweak=xts_tweak,
                                                                        command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "Creation of Encrypted BLT with uuid {} on F10".
                                           format(blt_uuid))
                else:
                    command_result = f10_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                        capacity=drive_size,
                                                                        block_size=4096,
                                                                        name=blt_name,
                                                                        uuid=blt_uuid[x],
                                                                        drive_uuid=drive_uuid_list[drive_index].strip(),
                                                                        command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "Creation of BLT with uuid {} on F10".format(blt_uuid))
                drive_index += 1

        if not deploy_vol and not skip_ctrlr_creation:
            fun_test.log("Volumes not deployed...")
            drive_dict = f10_storage_ctrl_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN",
                                                   command_duration=command_timeout)
            blt_uuid = {}
            count = 1
            for key in drive_dict["data"]:
                if key != "drives":
                    blt_uuid[count] = key
                    count += 1
            if count == 1:
                fun_test.test_assert(False, "F1_0 : BLT not found")
        '''
        # Use this to write the encrypted vol with data before export to RDS controller
        if not skip_ctrlr_creation:
            f10_pcie_ctrl = utils.generate_uuid()
            command_result = f10_storage_ctrl_obj.create_controller(transport="PCI",
                                                                    ctrlr_uuid=f10_pcie_ctrl,
                                                                    ctlid=0,
                                                                    huid=2,
                                                                    fnid=2,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_0 : Create PCIe controller")

            for x in xrange(1, total_ssd + 1):
                command_result = f10_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=blt_uuid[x],
                                                                                  ctrlr_uuid=f10_pcie_ctrl,
                                                                                  ns_id=x,
                                                                                  command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "F1_0 : Attach thin_blt_{} to PCIe ctrl".format(x))

            print "F10 attached thin_blt to PCIe controller"

            for x in xrange(1, total_ssd + 1):
                command_result = f10_storage_ctrl_obj.detach_volume_from_controller(ctrlr_uuid=f10_pcie_ctrl,
                                                                                    ns_id=x,
                                                                                    command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "F1_0 : Detach thin_blt_{} to PCIe ctrl".format(x))

            command_result = f10_storage_ctrl_obj.delete_controller(ctrlr_uuid=f10_pcie_ctrl,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_0 : Delete PCIe ctrl")
        '''
        if not skip_ctrlr_creation:
            fun_test.sleep("Here", 10)
            # Create PCIe controller on F1_1
            f11_pcie_ctrl = utils.generate_uuid()
            command_result = f11_storage_ctrl_obj.create_controller(transport="PCI",
                                                                    ctrlr_uuid=f11_pcie_ctrl,
                                                                    ctlid=0,
                                                                    huid=1,
                                                                    fnid=2,
                                                                    command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "F1_1 : Create PCIe controller")

            for x in xrange(1, total_ssd + 1):
                # Attach the BLT volume on F1_0 to RDS controller
                command_result = f10_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=blt_uuid[x],
                                                                                  ctrlr_uuid=f10_rds_ctrl,
                                                                                  ns_id=x,
                                                                                  command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "F1_0 : Attach thin_blt_{} to RDS ctrl".format(x))

                # Create RDS volume on F1_1
                f11_rds_vol[x] = utils.generate_uuid()
                rds_vol_name = "rds_vol_" + str(x)
                # xts_key = utils.generate_key(32)
                # xts_tweak = utils.generate_key(8)
                command_result = f11_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                    capacity=drive_size,
                                                                    block_size=4096,
                                                                    name=rds_vol_name,
                                                                    uuid=f11_rds_vol[x],
                                                                    remote_nsid=x,
                                                                    remote_ip=f10_vlan_ip,
                                                                    port=4420,
                                                                    command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "F1_1 : Created RDS vol with remote nsid {}".format(x))

                # Attach PCIe controller to host
                command_result = f11_storage_ctrl_obj.attach_volume_to_controller(vol_uuid=f11_rds_vol[x],
                                                                                  ctrlr_uuid=f11_pcie_ctrl,
                                                                                  ns_id=x,
                                                                                  command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "F1_1 : Attach RDS vol {} to PCIe ctrlr".format(x))

            f10_storage_ctrl_obj.disconnect()
            f11_storage_ctrl_obj.disconnect()

        fun_test.log_section("Storage config done")

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
        collect_artifacts = fun_test.shared_variables["collect_artifacts"]
        f10_storage_ctrl_obj = fun_test.shared_variables["f10_storage_ctrl_obj"]
        f11_storage_ctrl_obj = fun_test.shared_variables["f11_storage_ctrl_obj"]
        f10_stats_collector = CollectStats(f10_storage_ctrl_obj)
        f11_stats_collector = CollectStats(f11_storage_ctrl_obj)
        command_timeout = 5

        table_data_headers = ["NVMe device", "Num Jobs", "IO Depth", "Read IOPS", "Read Throughput in MB/s",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs"]
        table_data_cols = ["device_name", "num_jobs", "iodepth", "readiops", "readbw",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999"]
        table_data_rows = []
        row_data_dict = {}

        nvme_list_raw = f11_hosts[0]["handle"].sudo_command("nvme list -o json")
        if "failed to open" in nvme_list_raw.lower():
            nvme_list_raw = nvme_list_raw + "}"
            temp1 = nvme_list_raw.replace('\n', '')
            temp2 = re.search(r'{.*', temp1).group()
            nvme_list_dict = json.loads(temp2, strict=False)
        else:
            try:
                nvme_list_dict = json.loads(nvme_list_raw)
            except:
                nvme_list_raw = nvme_list_raw + "}"
                nvme_list_dict = json.loads(nvme_list_raw, strict=False)

        nvme_device_list = []
        for device in nvme_list_dict["Devices"]:
            if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"]:
                nvme_device_list.append(device["DevicePath"])
            elif "Unknown Device" in device["ProductName"]:
                if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
                    nvme_device_list.append(device["DevicePath"])

        host_nvme_device_count = len(nvme_device_list)

        fio_filename = str(':'.join(nvme_device_list))

        fio_num_jobs = 1 * host_nvme_device_count
        fio_runtime = 300
        fio_iodepth = 48
        artifact_poll_interval = 5
        # Run write test on disk
        fio_result = f11_hosts[0]["handle"].pcie_fio(filename=fio_filename,
                                                     rw="write",
                                                     bs=4096,
                                                     numjobs=fio_num_jobs,
                                                     iodepth=32,
                                                     direct=1,
                                                     prio=0,
                                                     size="100%",
                                                     cpus_allowed="8-11",
                                                     buffer_pattern="\\\"DEADBEEF\\\"",
                                                     name="fio_precondition",
                                                     timeout=600)
        fun_test.simple_assert(fio_result, message="Initial write test on all disks")

        test_type = "read"
        read_num_job = 4
        for nvme_device in nvme_device_list:
            fio_job_name = "fio_read_" + nvme_device
            device_name = nvme_device
            num_jobs = read_num_job
            iodepth = fio_iodepth
            row_data_list = []
            fio_result = f11_hosts[0]["handle"].pcie_fio(filename=nvme_device,
                                                         rw="read",
                                                         name=fio_job_name,
                                                         numjobs=read_num_job,
                                                         iodepth=fio_iodepth,
                                                         cpus_allowed="8-11",
                                                         direct=1,
                                                         prio=0,
                                                         verify="pattern",
                                                         verify_pattern="\\\"DEADBEEF\\\"",
                                                         runtime=fio_runtime,
                                                         timeout=fio_runtime + 180)
            fun_test.test_assert(fio_result, message="FIO job on {}".format(nvme_device))
            readbw = int(round(fio_result["read"]["bw"]/1000))
            readiops = int(round(fio_result["read"]["iops"]))
            if readiops < 700000:
                fun_test.add_checkpoint("IOPs for read test on {} is lesser than expected".format(nvme_device),
                                        result="FAILED")
            readclatency = fio_result["read"]["clatency"]
            readlatency90 = fio_result["read"]["latency90"]
            readlatency95 = fio_result["read"]["latency95"]
            readlatency99 = fio_result["read"]["latency99"]
            readlatency9999 = fio_result["read"]["latency9999"]
            for item in table_data_cols:
                row_data_list.append(eval(item))
            table_data_rows.append(row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}

        fun_test.add_table(panel_header="Fio perf data with crypto",
                           table_name=self.summary,
                           table_data=table_data)
        fun_test.log("Test done")

        fun_test.log("Test done")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(ConfigureRdsVol())
    ts.add_test_case(RunFioRds())
    ts.run()
