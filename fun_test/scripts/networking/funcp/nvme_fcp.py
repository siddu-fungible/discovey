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


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    arg1.command("hostname")
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def tune_host(host_obj):
    host_obj.sudo_command("/etc/init.d/irqbalance stop")
    host_obj.sudo_command("iptables -F")
    host_obj.sudo_command("ip6tables -F")


def get_nvme_device(host_obj):
    nvme_list_raw = host_obj.sudo_command("nvme list -o json")
    host_obj.disconnect()
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

    try:
        nvme_device_list = []
        for device in nvme_list_dict["Devices"]:
            if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"]:
                nvme_device_list.append(device["DevicePath"])
            elif "unknown device" in device["ProductName"].lower() or "null" in device["ProductName"].lower():
                if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
                    nvme_device_list.append(device["DevicePath"])
        fio_filename = str(':'.join(nvme_device_list))
    except:
        fio_filename = None

    return fio_filename


def storage_cleanup(storage_obj, command_timeout=5):
    # Clean the controllers
    controller_info = storage_obj.peek("storage/ctrlr/nvme")
    controller_data = controller_info["data"]
    for huid, huvalue in controller_data.iteritems():
        if huid != 7:
            for cntlid, cntvalue in huvalue.iteritems():
                for fnid, fnvalue in cntvalue.iteritems():
                    for key_name, key_value in fnvalue.iteritems():
                        if key_name.lower() == "name spaces":
                            if key_value:
                                volume_nsid_list = []
                                for list_value in key_value:
                                    for prop, value in list_value.iteritems():
                                        if prop.lower() == "uuid":
                                            volume_uuid = value
                                        if prop.lower() == "nsid":
                                            volume_nsid_list.append(value)
                        if key_name.lower() == "controller uuid":
                            if key_value:
                                controller_uuid = key_value
                                for vol_nsid in volume_nsid_list:
                                    command_result = storage_obj.detach_volume_from_controller(
                                        ctrlr_uuid=controller_uuid,
                                        ns_id=vol_nsid,
                                        command_duration=command_timeout)
                                    fun_test.simple_assert(command_result["status"],
                                                           "Detach controller with uuid {} & nsid {}".
                                                           format(controller_uuid, vol_nsid))
                                command_result = storage_obj.delete_controller(ctrlr_uuid=controller_uuid,
                                                                               command_duration=command_timeout)
                                fun_test.simple_assert(command_result["status"],
                                                       "Deleting controller with uuid {}".
                                                       format(controller_uuid))
    for huid, huvalue in controller_data.iteritems():
        if huid == 7:
            for cntlid, cntvalue in huvalue.iteritems():
                for fnid, fnvalue in cntvalue.iteritems():
                    for key_name, key_value in fnvalue.iteritems():
                        if key_name.lower() == "name spaces":
                            if key_value:
                                volume_nsid_list = []
                                for list_value in key_value:
                                    for prop, value in list_value.iteritems():
                                        if prop.lower() == "uuid":
                                            volume_uuid = value
                                        if prop.lower() == "nsid":
                                            volume_nsid_list.append(value)
                        if key_name.lower() == "controller uuid":
                            if key_value:
                                controller_uuid = key_value
                                for vol_nsid in volume_nsid_list:
                                    command_result = storage_obj.detach_volume_from_controller(
                                        ctrlr_uuid=controller_uuid,
                                        ns_id=vol_nsid,
                                        command_duration=command_timeout)
                                    fun_test.simple_assert(command_result["status"],
                                                           "Detach controller with uuid {} & nsid {}".
                                                           format(controller_uuid, vol_nsid))
                                command_result = storage_obj.delete_controller(ctrlr_uuid=controller_uuid,
                                                                               command_duration=command_timeout)
                                fun_test.simple_assert(command_result["status"],
                                                       "Deleting controller with uuid {}".
                                                       format(controller_uuid))

    # Clean the volumes
    volume_info = storage_obj.peek("storage/volumes")
    volume_data = volume_info["data"]
    for vol_type, vol_data in volume_data.iteritems():
        if vol_type != "VOL_TYPE_BLK_LOCAL_THIN":
            for vol_uuid, vol_stats in vol_data.iteritems():
                if vol_stats:
                    command_result = storage_obj.delete_volume(type=vol_type, uuid=vol_uuid,
                                                               command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "Deleting volume of type {} with uuid {}".
                                           format(vol_type, vol_uuid))

    for vol_type, vol_data in volume_data.iteritems():
        if vol_type == "VOL_TYPE_BLK_LOCAL_THIN":
            for vol_uuid, vol_stats in vol_data.iteritems():
                if vol_uuid == "drives":
                    pass
                else:
                    if vol_stats:
                        command_result = storage_obj.delete_volume(type=vol_type, uuid=vol_uuid,
                                                                   command_duration=command_timeout)
                        fun_test.simple_assert(command_result["status"], "Deleting volume of type {} with uuid {}".
                                               format(vol_type, vol_uuid))
    storage_obj.disconnect()


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
        fun_test.shared_variables["fio"] = {}

    def cleanup(self):
        f1_target_storage_obj = fun_test.shared_variables["f1_target_storage_obj"]
        f1_initiator_storage_obj = fun_test.shared_variables["f1_initiator_storage_obj"]
        storage_cleanup(f1_initiator_storage_obj)
        storage_cleanup(f1_target_storage_obj)


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
        if "rds_fcp" in job_inputs:
            rds_fcp = job_inputs["rds_fcp"]
            fun_test.shared_variables["rds_fcp"] = rds_fcp
            if rds_fcp:
                f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial " \
                         "--dpc-uart retimer={} rdstype=fcp --mgmt workload=storage".format(f10_retimer)
                f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial " \
                                 "--dpc-uart retimer={} rdstype=fcp --mgmt workload=storage".format(f11_retimer)
        else:
            fun_test.shared_variables["rds_fcp"] = False
        if "tcp_fcp" in job_inputs:
            tcp_fcp = job_inputs["tcp_fcp"]
            fun_test.shared_variables["tcp_fcp"] = tcp_fcp
        else:
            fun_test.shared_variables["tcp_fcp"] = False
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
            fun_test.shared_variables["collect_stats"] = True
        if "rds_conn" in job_inputs:
            fun_test.shared_variables["rds_conn"] = job_inputs["rds_conn"]
        else:
            fun_test.shared_variables["rds_conn"] = False
        if "f1_target" in job_inputs:
            fun_test.shared_variables["f1_target"] = job_inputs["f1_target"]
        else:
            fun_test.shared_variables["f1_target"] = "f10"
        if "rds_vol_transport" in job_inputs:
            fun_test.shared_variables["rds_vol_transport"] = unicode(job_inputs["rds_vol_transport"]).upper()
        else:
            fun_test.shared_variables["rds_vol_transport"] = False
        if "split_ssd" in job_inputs:
            fun_test.shared_variables["split_ssd"] = job_inputs["split_ssd"]
        else:
            fun_test.shared_variables["split_ssd"] = 0
        if "enable_debug" in job_inputs:
            if job_inputs["enable_debug"]:
                f1_0_boot_args += " module_log=fabrics_target:DEBUG,fabrics_host:DEBUG"
                f1_1_boot_args += " module_log=fabrics_target:DEBUG,fabrics_host:DEBUG"

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
            f10_instance = fs.get_f1(index=0)
            f11_instance = fs.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()

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

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

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
            f10_instance = fs_obj.get_f1(index=0)
            f11_instance = fs_obj.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()
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
        rds_fcp = fun_test.shared_variables["rds_fcp"]
        tcp_fcp = fun_test.shared_variables["tcp_fcp"]
        come_obj = fun_test.shared_variables["come_obj"]
        abstract_key = ""
        if rds_fcp or tcp_fcp:
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

            if not rds_fcp or not tcp_fcp:
                # Add static routes on Containers
                funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])

            fun_test.sleep(message="Waiting before ping tests", seconds=10)

            # Ping QFX from both F1s
            ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
            if rds_fcp or tcp_fcp:
                ping_dict = self.server_key["fs"][fs_name]["cc_pings_bgp"]

            for container in ping_dict:
                funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

            # Ping vlan to vlan
            funcp_obj.test_cc_pings_fs()

            # Print the tunnel info if its FCP
            if rds_fcp or tcp_fcp:
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
        split_ssd = fun_test.shared_variables["split_ssd"]
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

        # Storage Controller Objects
        f10_storage_ctrl_obj = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_ctrl_obj = fun_test.shared_variables["f11_storage_controller"]
        f1_target = fun_test.shared_variables["f1_target"]
        if f1_target == "f10":
            fun_test.log_section("Target is F10")
            f1_initiator = "f11"
            f1_target_storage_obj = f10_storage_ctrl_obj
            f1_initiator_storage_obj = f11_storage_ctrl_obj
            fun_test.shared_variables["f1_target_storage_obj"] = f1_target_storage_obj
            fun_test.shared_variables["f1_initiator_storage_obj"] = f1_initiator_storage_obj
            target_ip = f10_vlan_ip
            initiator_ip = f11_vlan_ip
            hu_id = [1, 3]
            fun_test.shared_variables["initiator_hosts"] = fun_test.shared_variables["f11_hosts"]
        elif f1_target == "f11":
            fun_test.log_section("Target is F11")
            f1_initiator = "f10"
            f1_target_storage_obj = f11_storage_ctrl_obj
            f1_initiator_storage_obj = f10_storage_ctrl_obj
            fun_test.shared_variables["f1_target_storage_obj"] = f1_target_storage_obj
            fun_test.shared_variables["f1_initiator_storage_obj"] = f1_initiator_storage_obj
            target_ip = f11_vlan_ip
            initiator_ip = f10_vlan_ip
            hu_id = [2, 1]
            fun_test.shared_variables["initiator_hosts"] = fun_test.shared_variables["f10_hosts"]

        # Stop udev services on host
        service_list = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in service_list:
            for host_obj in fun_test.shared_variables["initiator_hosts"]:
                service_status = host_obj["handle"].systemctl(service_name=service, action="stop")
                fun_test.simple_assert(service_status, "Stopping {} service on {}".format(service, host_obj["name"]))

        if not skip_ctrlr_creation:
            # Create IPCFG on F1_0
            command_result = f10_storage_ctrl_obj.ip_cfg(ip=f10_vlan_ip, port=controller_port)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_0 COMe")

            # Create IPCFG on F1_1
            command_result = f11_storage_ctrl_obj.ip_cfg(ip=f11_vlan_ip, port=controller_port)
            fun_test.test_assert(command_result["status"], "ip_cfg on F1_1 COMe")

            # Get list of drives on target
            drive_dict = f1_target_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                    command_duration=command_timeout)
            drive_uuid_list = sorted(drive_dict["data"].keys())
            target_drive_count = len(drive_uuid_list)

            fun_test.test_assert(expression=(target_drive_count >= total_ssd),
                                 message="SSD count on {} target of FS is {}, test requirement : {}".
                                 format(f1_target, target_drive_count, total_ssd))

            # Create RDS controller on target
            target_rds_ctrl = utils.generate_uuid()
            if fun_test.shared_variables["rds_vol_transport"]:
                controller_transport = fun_test.shared_variables["rds_vol_transport"]
            else:
                controller_transport = "RDS"
            command_result = f1_target_storage_obj.create_controller(ctrlr_uuid=target_rds_ctrl,
                                                                     transport=controller_transport,
                                                                     nqn="nqn1",
                                                                     port=controller_port,
                                                                     remote_ip=initiator_ip,
                                                                     command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"],
                                   "{} : Creation of RDS controller with uuid {}".format(f1_target, target_rds_ctrl))

        if deploy_vol:
            drive_index = 0
            initiator_rds_vol = {}
            blt_uuid = {}
            for x in xrange(1, total_ssd + 1):
                # Create BLT on target on each SSD & attach it to RDS controller
                blt_name = "thin_blt_" + str(x)
                blt_uuid[x] = utils.generate_uuid()
                command_result = f1_target_storage_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                     capacity=drive_size,
                                                                     block_size=block_size,
                                                                     name=blt_name,
                                                                     uuid=blt_uuid[x],
                                                                     drive_uuid=drive_uuid_list[drive_index].strip(),
                                                                     command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "Creation of BLT with uuid {} on {}".format(blt_uuid,
                                                                                                             f1_target))
                drive_index += 1
        if not deploy_vol and not skip_ctrlr_creation:
            fun_test.log("Volumes not deployed...")
            drive_dict = f1_target_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN",
                                                    command_duration=command_timeout)
            blt_uuid = {}
            count = 1
            for key in drive_dict["data"]:
                if key != "drives":
                    blt_uuid[count] = key
                    count += 1
            if count == 1:
                fun_test.test_assert(False, "{} : BLT not found".format(f1_target))

        if not skip_ctrlr_creation:
            # fun_test.sleep("Here", 10)
            # Create PCIe controller on Initiator
            initiator_pcie_ctrl = utils.generate_uuid()
            command_result = f1_initiator_storage_obj.create_controller(transport="PCI",
                                                                        ctrlr_uuid=initiator_pcie_ctrl,
                                                                        ctlid=0,
                                                                        huid=hu_id[0],
                                                                        fnid=2,
                                                                        command_duration=command_timeout)
            fun_test.simple_assert(command_result["status"], "{} : Create PCIe controller".format(f1_initiator))
            if total_ssd == 4 or split_ssd:
                initiator_pcie_ctrl_1 = utils.generate_uuid()
                command_result = f1_initiator_storage_obj.create_controller(transport="PCI",
                                                                            ctrlr_uuid=initiator_pcie_ctrl_1,
                                                                            ctlid=0,
                                                                            huid=hu_id[1],
                                                                            fnid=2,
                                                                            command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "{}: Create PCIe controller on HUID:{}".
                                       format(f1_initiator, hu_id[1]))

            for x in xrange(1, total_ssd + 1):
                # Attach the BLT volume on target to RDS controller
                command_result = f1_target_storage_obj.attach_volume_to_controller(vol_uuid=blt_uuid[x],
                                                                                   ctrlr_uuid=target_rds_ctrl,
                                                                                   ns_id=x,
                                                                                   command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "{} : Attach thin_blt_{} to RDS ctrl".format(f1_target,
                                                                                                              x))

                # Create RDS volume on initiator
                initiator_rds_vol[x] = utils.generate_uuid()
                rds_vol_name = "rds_vol_" + str(x)
                if fun_test.shared_variables["rds_conn"] and not fun_test.shared_variables["rds_vol_transport"]:
                    rds_conn = fun_test.shared_variables["rds_conn"]
                    command_result = f1_initiator_storage_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                            capacity=drive_size,
                                                                            block_size=block_size,
                                                                            name=rds_vol_name,
                                                                            uuid=initiator_rds_vol[x],
                                                                            remote_nsid=x,
                                                                            remote_ip=target_ip,
                                                                            port=controller_port,
                                                                            connections=rds_conn,
                                                                            command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "{} : Created RDS vol using {} connections with remote nsid {}".
                                           format(f1_initiator, rds_conn, x))
                elif fun_test.shared_variables["rds_vol_transport"] and not fun_test.shared_variables["rds_conn"]:
                    rds_vol_transport = fun_test.shared_variables["rds_vol_transport"]
                    command_result = f1_initiator_storage_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                            capacity=drive_size,
                                                                            block_size=block_size,
                                                                            name=rds_vol_name,
                                                                            uuid=initiator_rds_vol[x],
                                                                            remote_nsid=x,
                                                                            remote_ip=target_ip,
                                                                            port=controller_port,
                                                                            transport=rds_vol_transport,
                                                                            command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "{} : Created RDS vol using {} transport with remote nsid {}".
                                           format(f1_initiator, rds_vol_transport, x))
                elif fun_test.shared_variables["rds_vol_transport"] and fun_test.shared_variables["rds_conn"]:
                    rds_conn = fun_test.shared_variables["rds_conn"]
                    rds_vol_transport = fun_test.shared_variables["rds_vol_transport"]
                    command_result = f1_initiator_storage_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                            capacity=drive_size,
                                                                            block_size=block_size,
                                                                            name=rds_vol_name,
                                                                            uuid=initiator_rds_vol[x],
                                                                            remote_nsid=x,
                                                                            remote_ip=target_ip,
                                                                            port=controller_port,
                                                                            transport=rds_vol_transport,
                                                                            connections=rds_conn,
                                                                            command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "{} : Created RDS vol using {} transport : {} connections with "
                                           "remote nsid {}".
                                           format(f1_initiator, rds_vol_transport, rds_conn, x))
                else:
                    command_result = f1_initiator_storage_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                            capacity=drive_size,
                                                                            block_size=block_size,
                                                                            name=rds_vol_name,
                                                                            uuid=initiator_rds_vol[x],
                                                                            remote_nsid=x,
                                                                            remote_ip=target_ip,
                                                                            port=controller_port,
                                                                            command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "{} : Created RDS vol with remote nsid {}".format(f1_initiator, x))

                # Attach PCIe controller to host
                if total_ssd == 4:
                    if x > 2:
                        initiator_ctrl = initiator_pcie_ctrl_1
                        fun_test.log("PCIe controller is HUID 3")
                    else:
                        initiator_ctrl = initiator_pcie_ctrl
                        fun_test.log("PCIe controller is HUID 1")
                elif split_ssd:
                    if x > 1:
                        initiator_ctrl = initiator_pcie_ctrl_1
                        fun_test.log("PCIe controller is HUID 3")
                    else:
                        initiator_ctrl = initiator_pcie_ctrl
                        fun_test.log("PCIe controller is HUID 1")
                else:
                    initiator_ctrl = initiator_pcie_ctrl
                    fun_test.log("Only one PCIe controller on HUID 1")

                command_result = f1_initiator_storage_obj.attach_volume_to_controller(vol_uuid=initiator_rds_vol[x],
                                                                                      ctrlr_uuid=initiator_ctrl,
                                                                                      ns_id=x,
                                                                                      command_duration=command_timeout)
                fun_test.simple_assert(command_result["status"], "{} : Attach RDS vol {} to PCIe ctrlr".
                                       format(f1_initiator, x))

            f1_initiator_storage_obj.disconnect()
            f1_target_storage_obj.disconnect()

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
        initiator_hosts = fun_test.shared_variables["initiator_hosts"]
        come_obj = fun_test.shared_variables["come_obj"]
        total_ssd = fun_test.shared_variables["total_ssd"]
        f1_target_storage_obj = fun_test.shared_variables["f1_target_storage_obj"]
        f1_initiator_storage_obj = fun_test.shared_variables["f1_initiator_storage_obj"]
        skip_precondition = fun_test.shared_variables["skip_precondition"]
        split_ssd = fun_test.shared_variables["split_ssd"]
        collect_stats = fun_test.shared_variables["collect_stats"]

        table_data_headers = ["Block_Size", "IOPs", "BW in Gbps"]
        table_data_cols = ["read_block_size", "total_read_iops", "total_read_bw"]

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
        if "fio_runtime" in job_inputs:
            self.fio_cmd_args["runtime"] = job_inputs["fio_runtime"]

        if total_ssd == 4 or split_ssd:
            host_dict = {}
            for host in initiator_hosts:
                host_dict[host["name"]] = {}
                host_dict[host["name"]]["handle"] = host["handle"]
                host_dict[host["name"]]["nvme_device"] = get_nvme_device(host["handle"])
                if not host_dict[host["name"]["nvme_device"]]:
                    host_dict[host["name"]]["handle"].command("dmesg")
                    fun_test.simple_assert(False, "NVMe device not found on {}".format(host["name"]))
                host_dict[host["name"]]["handle"].command("dmesg")
                host_dict[host["name"]]["cpu_list"] = get_numa(host["handle"])
                tune_host(host["handle"])
        else:
            host_dict = {}
            host_dict[initiator_hosts[0]["name"]] = {}
            host_dict[initiator_hosts[0]["name"]]["handle"] = initiator_hosts[0]["handle"]
            temp_nvme_devices = get_nvme_device(initiator_hosts[0]["handle"])
            if not temp_nvme_devices:
                initiator_hosts[0]["handle"].command("dmesg")
                fun_test.simple_assert(False, "NVMe device not found on {}".format(initiator_hosts[0]["name"]))
            initiator_hosts[0]["handle"].command("dmesg")
            temp_nvme_dev_list = temp_nvme_devices.split(":")[:total_ssd]
            host_dict[initiator_hosts[0]["name"]]["nvme_device"] = ":".join(temp_nvme_dev_list)
            host_dict[initiator_hosts[0]["name"]]["cpu_list"] = get_numa(initiator_hosts[0]["handle"])
            tune_host(initiator_hosts[0]["handle"])

        if not skip_precondition:
            # Run write test on disk
            thread_id = {}
            x = 1
            wait_time = total_ssd
            fio_output = {}
            for precond_iter in xrange(0, 2):
                for host in host_dict:
                    fio_filename = host_dict[host]["nvme_device"]
                    precondition_fio_num_jobs = len(fio_filename.split(":"))
                    if precondition_fio_num_jobs > 2:
                        # 64 max IODepth for write test. More than this write fail
                        max_write_iodepth = 64
                        set_iodepth = int(max_write_iodepth / precondition_fio_num_jobs)
                        self.precondition_args["iodepth"] = set_iodepth
                    host_clone = host_dict[host]["handle"].clone()
                    thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 host_index=x,
                                                                 arg1=host_clone,
                                                                 filename=fio_filename,
                                                                 numjobs=precondition_fio_num_jobs,
                                                                 rw="write",
                                                                 name="precondition_" + str(host),
                                                                 cpus_allowed=host_dict[host]["cpu_list"],
                                                                 **self.precondition_args)
                    fun_test.sleep("Fio threadzz", seconds=1)
                    wait_time -= 1
                    x += 1

                for ids in thread_id:
                    try:
                        fun_test.log("Joining fio thread {}".format(ids))
                        fun_test.join_thread(fun_test_thread_id=thread_id[ids])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][ids])
                        fun_test.test_assert(fun_test.shared_variables["fio"][ids], "Fio threaded test")
                        fio_output[ids] = {}
                        fio_output[ids] = fun_test.shared_variables["fio"][ids]
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fun_test.log("FIO Command Output for volume {}:\n {}".format(ids, fio_output[ids]))

            fun_test.sleep("Pre-condition done", 10)

        '''
        FIO PARSED OUTPUT FORMAT
        {'latency': 4850, 'latency9999': 111673, 'io_bytes': 51883728896, 'latency9950': 63700,
         'latency99': 55836, 'iops': 105531.333833, 'bw': 422125, 'latency90': 16318,
          'runtime': 120030, 'latency95': 30539, 'clatency': 4847}'''

        test_type = "randread"
        stats_collect_count = self.fio_cmd_args["runtime"] / self.stats_interval
        table_data_rows = []

        if not numjobs_set and total_ssd != 4:
            self.fio_cmd_args["numjobs"] = 8 * total_ssd
            fio_read_jobs = self.fio_cmd_args["numjobs"]
        else:
            fio_read_jobs = self.fio_cmd_args["numjobs"]

        fio_iodepth = self.fio_cmd_args["iodepth"]

        fio_job_name = "ssd_{}_{}_{}_".format(test_type, fio_read_jobs, fio_iodepth)
        stats_collection_details = self.stats_collect_details

        # Starting the thread to collect the vp_utils stats and resource_bam stats for the current iteration
        if collect_stats:
            file_suffix_1 = "ssd_numjobs_{}_iodepth_{}_target.txt".format(fio_read_jobs, fio_iodepth)
            file_suffix_2 = "ssd_numjobs_{}_iodepth_{}_initiator.txt".format(fio_read_jobs, fio_iodepth)
            stats_collect_details_target = copy.deepcopy(stats_collection_details)
            stats_collect_details_initiator = copy.deepcopy(stats_collection_details)

            # Collect stats from target
            for index, stat_detail in enumerate(stats_collect_details_target):
                func = stat_detail.keys()[0]
                stats_collect_details_target[index][func]["count"] = stats_collect_count
            fun_test.log("Different target stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format(fio_read_jobs, stats_collect_details_target))
            f1_target_storage_obj.verbose = False
            target_stats_obj = CollectStats(storage_controller=f1_target_storage_obj)
            target_stats_obj.start(file_suffix_1, stats_collect_details_target)
            fun_test.log("Different target stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format(fio_read_jobs, stats_collect_details_target))

            # Collect stats from initiator
            for index, stat_detail in enumerate(stats_collect_details_initiator):
                func = stat_detail.keys()[0]
                stats_collect_details_initiator[index][func]["count"] = stats_collect_count
            fun_test.log("Different initiator stats collection thread details for the current IO depth {} "
                         "before starting them:\n{}".format(fio_read_jobs, stats_collect_details_initiator))
            f1_initiator_storage_obj.verbose = False
            initiator_stats_obj = CollectStats(storage_controller=f1_initiator_storage_obj)
            initiator_stats_obj.start(file_suffix_2, stats_collect_details_initiator)
            fun_test.log("Different initiator stats collection thread details for the current IO depth {} "
                         "after starting them:\n{}".format(fio_read_jobs, stats_collect_details_initiator))
        else:
            f1_target_storage_obj.disconnect()
            f1_initiator_storage_obj.disconnect()
            fun_test.critical("Stats collection disabled")

        thread_id = {}
        x = 1
        wait_time = total_ssd
        fio_output = {}
        iops_sum = 0
        bw_sum = 0
        for host in host_dict:
            fio_filename = host_dict[host]["nvme_device"]
            host_clone = host_dict[host]["handle"].clone()
            thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                         func=fio_parser,
                                                         host_index=x,
                                                         arg1=host_clone,
                                                         filename=fio_filename,
                                                         rw="randread",
                                                         name=fio_job_name + str(host),
                                                         cpus_allowed=host_dict[host]["cpu_list"],
                                                         **self.fio_cmd_args)
            fun_test.sleep("Fio threadzz", seconds=1)
            wait_time -= 1
            x += 1
        for ids in thread_id:
            try:
                fun_test.log("Joining fio thread {}".format(ids))
                fun_test.join_thread(fun_test_thread_id=thread_id[ids])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][ids])
                fun_test.test_assert(fun_test.shared_variables["fio"][ids], "Fio threaded test")
                fio_output[ids] = {}
                fio_output[ids] = fun_test.shared_variables["fio"][ids]
                iops_sum += fio_output[ids]["read"]["iops"]
                bw_sum += fio_output[ids]["read"]["bw"]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO read Output for volume {}:\n {}".format(ids, fio_output[ids]))

        if collect_stats:
            target_stats_obj.stop(stats_collect_details_target)
            initiator_stats_obj.stop(stats_collect_details_initiator)
            f1_target_storage_obj.verbose = True
            f1_initiator_storage_obj.verbose = True
            f1_target_storage_obj.disconnect()
            f1_initiator_storage_obj.disconnect()

        read_block_size = self.fio_cmd_args["bs"]
        total_read_iops = iops_sum
        total_read_bw = bw_sum/125000
        row_data_list = []
        for item in table_data_cols:
            row_data_list.append(eval(item))
        table_data_rows.append(row_data_list)
        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        for x in range(0, 2):
            if x == 0:
                stats_collect_details = stats_collect_details_target
            elif x == 1:
                stats_collect_details = stats_collect_details_initiator

            for index, value in enumerate(stats_collect_details):
                for func, arg in value.iteritems():
                    filename = arg.get("output_file")
                    if filename:
                        if func == "vp_utils":
                            fun_test.add_auxillary_file(description="F1_{} VP Utilization - IO depth {}".
                                                        format(x, fio_read_jobs),
                                                        filename=filename)
                        if func == "per_vp":
                            fun_test.add_auxillary_file(description="F1_{} Per VP Stats - IO depth {}".
                                                        format(x, fio_read_jobs), filename=filename)
                        if func == "eqm_stats":
                            fun_test.add_auxillary_file(description="F1_{} EQM Stats - IO depth {}".
                                                        format(x, fio_read_jobs), filename=filename)
                        if func == "fcp_stats":
                            fun_test.add_auxillary_file(description="F1_{} FCP Stats - IO depth {}".
                                                        format(x, fio_read_jobs), filename=filename)
        fun_test.add_table(panel_header="NVMe FCP Sanity Numbers",
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
