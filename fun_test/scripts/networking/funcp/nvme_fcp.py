from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from asset.asset_manager import *
import re
import ipaddress
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform


def add_to_data_base(value_dict):
    unit_dict = {
        "read_iops_unit": PerfUnit.UNIT_OPS,
        "read_bw_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "read_latency_avg_unit": PerfUnit.UNIT_USECS,
        "read_latency_50_unit": PerfUnit.UNIT_USECS,
        "read_latency_90_unit": PerfUnit.UNIT_USECS,
        "read_latency_95_unit": PerfUnit.UNIT_USECS,
        "read_latency_99_unit": PerfUnit.UNIT_USECS,
        "read_latency_9950_unit": PerfUnit.UNIT_USECS,
        "read_latency_9999_unit": PerfUnit.UNIT_USECS,
    }

    value_dict["date_time"] = get_data_collection_time()
    value_dict["version"] = fun_test.get_version()
    print "HI there, the version is {}".format(value_dict["version"])
    value_dict["platform"] = FunPlatform.F1
    model_name = "NvmeFcpPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
        print "used generic helper to add an entry"
    except Exception as ex:
        fun_test.critical(str(ex))


def get_numa(host_obj):
    device_id = host_obj.lspci(grep_filter="1dad")
    if not device_id:
        device_id = host_obj.lspci(grep_filter="Fungible")
    lspci_verbose_mode = host_obj.lspci(slot=device_id[0]["id"], verbose=True)
    numa_number = lspci_verbose_mode[0]["numa_node"]
    # TODO
    # FIX this...if numa 0 then skip core 0 & its HT
    # if numa_number == 0:
    numa_cores = host_obj.lscpu(grep_filter="node{}".format(numa_number))
    cpu_list = numa_cores.values()[0]
    return cpu_list


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
        topology_helper = TopologyHelper()
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
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} --mgmt workload=storage".format(f10_retimer)
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} --mgmt workload=storage".format(f11_retimer)

        # module_log=tcp:DEBUG,fabrics_host:INFO,rdsvol:INFO

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
                f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial " \
                         "--dpc-uart retimer={} rdstype=fcp --mgmt workload=storage".format(f10_retimer)
                f1_1_boot_args = "app=load_mods cc_huid=2 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer={} rdstype=fcp --mgmt workload=storage".format(f11_retimer)
        else:
            fun_test.shared_variables["enable_fcp"] = False
        if "total_ssd" in job_inputs:
            total_ssd = job_inputs["total_ssd"]
            fun_test.shared_variables["total_ssd"] = total_ssd
        else:
            fun_test.shared_variables["total_ssd"] = 1
        if "skip_ctrlr_creation" in job_inputs:
            skip_ctrlr_creation = job_inputs["skip_ctrlr_creation"]
            fun_test.shared_variables["skip_ctrlr_creation"] = skip_ctrlr_creation
        else:
            fun_test.shared_variables["skip_ctrlr_creation"] = False
        if "skip_precondition" in job_inputs:
            fun_test.shared_variables["skip_precondition"] = job_inputs["skip_precondition"]
        else:
            fun_test.shared_variables["skip_precondition"] = False
        if "collect_stats" in job_inputs:
            fun_test.shared_variables["collect_stats"] = job_inputs["collect_stats"]
        else:
            fun_test.shared_variables["collect_stats"] = False

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
            if "fs-45" in fs_name or "fs-alibaba-demo" in fs_name:
                come_obj.command("/home/fun/mks/restart_docker_service.sh")

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
                fun_test.sleep("FCP Configured", 60)

                # if "openconfig-fcp:fcp-tunnel[ftep='4.4.4.4'][tunnel-type='0']" in f10_ftep_status:
                #     print "********** BGP is up **********"
                #     print f10_ftep_status
                # else:
                #     fun_test.critical(message="FTEP not seen on F10")
                # if "openconfig-fcp:fcp-tunnel[ftep='3.3.3.3'][tunnel-type='0']" in f11_ftep_status:
                #     print f11_ftep_status
                # else:
                #     fun_test.critical(message="FTEP not seen on F11")

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

        config_file = fun_test.get_script_name_without_ext() + ".json"
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict["GenericParams"].items():
            setattr(self, k, v)

        drive_size = self.blt_details["capacity"]
        command_timeout = self.command_timeout
        controller_port = self.controller_port
        block_size = self.blt_details["block_size"]

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
            command_result = f10_storage_ctrl_obj.ip_cfg(ip=f10_vlan_ip, port=controller_port)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_0 COMe")

            # Create IPCFG on F1_1
            command_result = f11_storage_ctrl_obj.ip_cfg(ip=f11_vlan_ip, port=controller_port)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_1 COMe")

            # Get list of drives on F1_1
            drive_dict = f10_storage_ctrl_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                   command_duration=command_timeout)
            drive_uuid_list = sorted(drive_dict["data"].keys())
            f10_drive_count = len(drive_uuid_list)

            fun_test.test_assert(expression=(f10_drive_count >= total_ssd),
                                 message="SSD count on F10 of FS is {}, test requirement : {}".
                                 format(f10_drive_count, total_ssd))

            # Create RDS controller on F1_0
            f10_rds_ctrl = utils.generate_uuid()
            command_result = f10_storage_ctrl_obj.create_controller(ctrlr_uuid=f10_rds_ctrl,
                                                                    transport="RDS",
                                                                    nqn="nqn1",
                                                                    port=controller_port,
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
                command_result = f10_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                    capacity=drive_size,
                                                                    block_size=block_size,
                                                                    name=blt_name,
                                                                    uuid=blt_uuid[x],
                                                                    drive_uuid=drive_uuid_list[drive_index].strip(),
                                                                    command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "Creation of BLT with uuid {} on F10".format(blt_uuid))
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

        if not skip_ctrlr_creation:
            # fun_test.sleep("Here", 10)
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
                command_result = f11_storage_ctrl_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                    capacity=drive_size,
                                                                    block_size=block_size,
                                                                    name=rds_vol_name,
                                                                    uuid=f11_rds_vol[x],
                                                                    remote_nsid=x,
                                                                    remote_ip=f10_vlan_ip,
                                                                    port=controller_port,
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
        total_ssd = fun_test.shared_variables["total_ssd"]
        f10_storage_ctrl_obj = fun_test.shared_variables["f10_storage_ctrl_obj"]
        f11_storage_ctrl_obj = fun_test.shared_variables["f11_storage_ctrl_obj"]
        f10_stats_collector = CollectStats(f10_storage_ctrl_obj)
        f11_stats_collector = CollectStats(f11_storage_ctrl_obj)
        skip_precondition = fun_test.shared_variables["skip_precondition"]
        collect_stats = fun_test.shared_variables["collect_stats"]

        table_data_headers = ["Devices", "Block_Size", "IOPs", "BW in Gbps"]
        table_data_cols = ["devices", "read_block_size", "total_read_iops", "total_read_bw"]

        config_file = fun_test.get_script_name_without_ext() + ".json"
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict["GenericParams"].items():
            setattr(self, k, v)
        command_timeout = self.command_timeout

        job_inputs = fun_test.get_job_inputs()
        if "iodepth" in job_inputs:
            self.fio_cmd_args["iodepth"] = job_inputs["iodepth"]
        if "numjobs" in job_inputs:
            self.fio_cmd_args["numjobs"] = job_inputs["numjobs"]
            numjobs_set = True
        else:
            numjobs_set = False

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

        fun_test.test_assert(nvme_device_list, "NVMe devices on host")
        print "***************************"
        print " NVMe Devices found "
        print "***************************"
        print nvme_device_list

        host_nvme_device_count = len(nvme_device_list)
        fio_filename = str(':'.join(nvme_device_list))

        if total_ssd != host_nvme_device_count:
            if total_ssd == 1:
                fio_filename = nvme_device_list[0]
            else:
                fio_filename = str(':'.join(nvme_device_list[:total_ssd]))

        print "Running traffic on"
        print fio_filename

        try:
            if self.precondition_args["numjobs"]:
                precondition_fio_num_jobs = self.precondition_args["numjobs"]
        except:
            precondition_fio_num_jobs = 1 * host_nvme_device_count

        if not skip_precondition:
            # Run write test on disk
            fio_result = f11_hosts[0]["handle"].pcie_fio(filename=fio_filename,
                                                         rw="write",
                                                         numjobs=precondition_fio_num_jobs,
                                                         timeout=1200,
                                                         **self.precondition_args)
            fun_test.simple_assert(fio_result, message="Initial write test on all disks")

        '''
        FIO PARSED OUTPUT FORMAT
        {'latency': 4850, 'latency9999': 111673, 'io_bytes': 51883728896, 'latency9950': 63700,
         'latency99': 55836, 'iops': 105531.333833, 'bw': 422125, 'latency90': 16318,
          'runtime': 120030, 'latency95': 30539, 'clatency': 4847}'''
        test_type = "read"
        stats_collect_count = self.fio_cmd_args["runtime"] / self.stats_interval
        table_data_rows = []
        cpu_list = get_numa(f11_hosts[0]["handle"])
        for x in range(1, total_ssd + 1):
            if x == 1:
                fio_filename = nvme_device_list[0]
            else:
                fio_filename = str(':'.join(nvme_device_list[:x]))
            if not numjobs_set:
                self.fio_cmd_args["numjobs"] = 8 * x
                fio_read_jobs = self.fio_cmd_args["numjobs"]
            else:
                fio_read_jobs = self.fio_cmd_args["numjobs"]
            fio_job_name = "{}_ssd_{}_{}".format(x, test_type,
                                                 fio_read_jobs)

            # Starting the thread to collect the vp_utils stats and resource_bam stats for the current iteration
            if collect_stats:
                file_suffix = "{}_ssd_iodepth_{}_f10.txt".format(x, fio_read_jobs)
                for index, stat_detail in enumerate(self.stats_collect_details):
                    func = stat_detail.keys()[0]
                    self.stats_collect_details[index][func]["count"] = stats_collect_count
                fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                             "them:\n{}".format(fio_read_jobs, self.stats_collect_details))
                f10_storage_ctrl_obj.verbose = False
                self.f10_stats_obj = CollectStats(storage_controller=f10_storage_ctrl_obj)
                self.f10_stats_obj.start(file_suffix, self.stats_collect_details)
                fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                             "them:\n{}".format(fio_read_jobs, self.stats_collect_details))
            else:
                f10_storage_ctrl_obj.disconnect()
                f11_storage_ctrl_obj.disconnect()
                fun_test.critical("Stats collection disabled")
            try:
                fio_result = f11_hosts[0]["handle"].pcie_fio(filename=fio_filename,
                                                             rw="read",
                                                             name=fio_job_name,
                                                             cpus_allowed=cpu_list,
                                                             **self.fio_cmd_args)
                fun_test.log("FIO result {}".format(fio_result))
                fun_test.test_assert(fio_result, message="FIO job {}".format(fio_job_name))
            except:
                fun_test.critical("FIO test failed")

            if collect_stats:
                self.f10_stats_obj.stop(self.stats_collect_details)
                f10_storage_ctrl_obj.verbose = True
                f11_storage_ctrl_obj.verbose = True
                f10_storage_ctrl_obj.disconnect()
                f11_storage_ctrl_obj.disconnect()

            read_block_size = self.fio_cmd_args["bs"]
            total_read_iops = fio_result["read"]["iops"]
            total_read_bw = fio_result["read"]["bw"]/125000
            devices = fio_filename
            row_data_list = []
            for item in table_data_cols:
                row_data_list.append(eval(item))
            table_data_rows.append(row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}

            for index, value in enumerate(self.stats_collect_details):
                for func, arg in value.iteritems():
                    filename = arg.get("output_file")
                    if filename:
                        if func == "vp_utils":
                            fun_test.add_auxillary_file(description="F1 VP Utilization - IO depth {}".
                                                        format(fio_read_jobs),
                                                        filename=filename)
                        if func == "per_vp":
                            fun_test.add_auxillary_file(description="F1 Per VP Stats - IO depth {}".
                                                        format(fio_read_jobs), filename=filename)
                        if func == "eqm_stats":
                            fun_test.add_auxillary_file(description="F1 EQM Stats - IO depth {}".
                                                        format(fio_read_jobs), filename=filename)
                        if func == "fcp_stats":
                            fun_test.add_auxillary_file(description="F1 FCP Stats - IO depth {}".
                                                        format(fio_read_jobs), filename=filename)

        fun_test.add_table(panel_header="NVMe FCP Sanity",
                           table_name=self.summary,
                           table_data=table_data)

        # Compute expected IOPs
        if total_ssd == 1:
            exp_iops = 600
        else:
            exp_iops = 600 * total_ssd
        current_read_iops = total_read_iops / 1000
        fun_test.log("The current read IOPs: {}".format(current_read_iops))
        fun_test.log("The expected read IOPs: {}".format(exp_iops))
        # fun_test.simple_assert(expression=(current_read_iops > exp_iops),
        #                        message="Expected Read IOPs")

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
