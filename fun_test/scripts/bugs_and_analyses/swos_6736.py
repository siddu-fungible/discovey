from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.host.linux import *
from lib.templates.security.xts_openssl_template import XtsOpenssl
from asset.asset_manager import *
import ipaddress

def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()

class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        fun_test.shared_variables["xts_ssl"] = True

    def cleanup(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        for host in host_dict["f1_0"]:
            host.disconnect()
        for host in host_dict["f1_1"]:
            host.disconnect()


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
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=6 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=6 workload=storage"

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
            abstract_json_file0 = fun_test.get_script_parent_directory() + '/' + \
                                  self.server_key["fs"][fs_name][abstract_key]["F1-0"]
            abstract_json_file1 = fun_test.get_script_parent_directory() + '/' + \
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


class CryptoCore(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        self.host_obj = host_dict["f1_0"][0]
        skip_ctrlr_creation = fun_test.shared_variables["skip_ctrlr_creation"]
        total_ssd = fun_test.shared_variables["total_ssd"]
        come_obj = fun_test.shared_variables["come_obj"]

        self.qemu = QemuStorageTemplate(host=self.host_obj, dut=1)

        # Stop services on host
        self.qemu.stop_host_services()
        write_size = 4096
        data_size = 8192
        self.blt_block_size = 4096
        self.blt_uuid = utils.generate_uuid()
        self.command_timeout = 5
        self.storage_controller = StorageController(target_ip=come_obj.host_ip, target_port=40220)
        self.storage_controller_remote = StorageController(target_ip=come_obj.host_ip, target_port=40221)
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["storage_controller_remote"] = self.storage_controller_remote

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

        self.storage_controller = StorageController(target_ip=come_obj.host_ip, target_port=40220)
        self.storage_controller_remote = StorageController(target_ip=come_obj.host_ip, target_port=40221)
        if not skip_ctrlr_creation:
            # Create IPCFG on F1_0
            command_result = self.storage_controller.ip_cfg(ip=f10_vlan_ip, port=4420)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_0 COMe")

            # Create IPCFG on F1_1
            command_result = self.storage_controller_remote.ip_cfg(ip=f11_vlan_ip, port=4420)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_1 COMe")

            # Get list of drives on F1_1
            drive_dict = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                   command_duration=self.command_timeout)
            drive_uuid_list = sorted(drive_dict["data"].keys())
            f10_drive_count = len(drive_uuid_list)

            if total_ssd > len(drive_uuid_list):
                fun_test.test_assert_expected(False, "SSD count on FS: {} lesser than requirement : {}".
                                              format(total_ssd, f10_drive_count))
        num_raw_vol = 1
        num_encrypted_vol = 1
        num_rds_vol = 1
        num_rds_encrypted_vol =1
        self.raw_encryp_uuid = {}
        self.raw_uuid = {}

        self.rds_encryp_uuid_f1_1 = {}
        self.raw_uuid_f1_1 = {}


        self.rds_encryp_uuid = {}
        self.rds_raw_uuid = {}



        if not fun_test.shared_variables["xts_ssl"]:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)
            install_status = self.xts_ssl_template.install_ssl()
            fun_test.test_assert(install_status, "Openssl installation")
            fun_test.shared_variables["xts_ssl"] = True
        else:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)

        # Create a BLT with encryption using 256 bit key
        rds_xts_key = {}
        rds_xts_tweak = {}
        xts_key = utils.generate_key(length=32)
        xts_tweak = utils.generate_key(length=8)
        self.blt_capacity = 5368709120
        #self.blt_capacity = 10737418240


        print("**********************************")
        print("RDS controller on F1_1 ")
        print("**********************************\n")
        # Create RDS controller on F1_1
        self.rds_ctrlr_uuid = utils.generate_uuid()
        command_result = self.storage_controller_remote.create_controller(ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                   transport="RDS",
                                                                   remote_ip=f10_vlan_ip,
                                                                   nqn="nqn-1",
                                                                   port=4420,
                                                                   command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"],
                               "Creation of RDS controller with uuid {}".format(self.rds_ctrlr_uuid))

        print("**********************************")
        print("Creating volumes on F1_1")
        print("**********************************\n")
        # Creating volumes on F1_1
        # Creating encrypted volumes on F1_1

        # Creating raw volumes on F1_1
        for i in range(1, num_rds_vol + 1, 1):
            self.raw_uuid_f1_1[i] = utils.generate_uuid()
            command_result = self.storage_controller_remote.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=self.blt_capacity,
                                                                          block_size=self.blt_block_size,
                                                                          name="thin_raw_block" + str(i),
                                                                          uuid=self.raw_uuid_f1_1[i],
                                                                          command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "BLT creation on F1_1 with uuid {}".
                                   format(self.raw_uuid_f1_1))
        print("**********************************")
        print("Attaching volumes on F1_1")
        print("**********************************\n")



        for i in range(1, num_raw_vol+1, 1):
            cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller_remote.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                             ns_id=1,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to RDS controller")

        print("**********************************")
        print("Creating RDS volumes on F1_0")
        print("**********************************\n")
        # Creating RDS volumes
        # Creating encrypted RDS volume on F1_0
        # Creating encrypted RDS volume on F1_0

        for i in range(1, num_rds_encrypted_vol + 1, 1):
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                   capacity=self.blt_capacity,
                                                                   block_size=self.blt_block_size,
                                                                   uuid=self.raw_uuid_f1_1[i],
                                                                   name="rds-block1",
                                                                   remote_nsid=1,
                                                                   remote_ip=f11_vlan_ip,
                                                                   port=4420,
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                 format(self.raw_uuid_f1_1))

        print("**********************************")
        print("Creating PCIe controller on F1_0")
        print("**********************************\n")

        # Create a PCIe controller
        self.controller_uuid = utils.generate_uuid()
        command_result = self.storage_controller.create_controller(ctrlr_uuid=self.controller_uuid,
                                                                   transport="PCI",
                                                                   fnid=2,
                                                                   ctlid=0,
                                                                   huid=2,
                                                                   command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"],
                               "Creation of PCIe controller with uuid {}".format(self.controller_uuid))

        print("**********************************")
        print("Attaching RDS volumes on F1_0")
        print("**********************************\n")

        num_vol = num_encrypted_vol + num_raw_vol
        #nsid = i+1
        nsid =1
        for i in range(1, num_encrypted_vol+1, 1):
            cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.controller_uuid,
                                                                             ns_id=nsid,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to PCIe controller")
            nsid +=1

    def cleanup(self):
        pass


class VolumeCreation(CryptoCore):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create BLT and RDS volumes on local F1_0",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT volumes with encryption enabled and encryption disabled.
                              3. Create a RDS volumes with encryption enabled and encryption disabled.
                              ''')



class RunFioRds(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Run fio traffic from host",
                              steps="""
                              1. Using fio write specific pattern to all volumes.
                              2. Using fio read back the pattern and verify correctness.
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.storage_controller_remote = fun_test.shared_variables["storage_controller_remote"]

        nvme_list_raw = f10_hosts[0]["handle"].sudo_command("nvme list -o json")
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
        print(fio_filename)
        f10_hosts[0]["handle"].sudo_command("mkfs.ext4 {}".format(fio_filename))
        fun_test.log("Test done")


    def cleanup(self):
        pass


if __name__ == "__main__":
    crypto_script = ScriptSetup()
    crypto_script.add_test_case(BringupSetup())
    crypto_script.add_test_case(NicEmulation())
    crypto_script.add_test_case(VolumeCreation())
    crypto_script.add_test_case(RunFioRds())
    crypto_script.run()