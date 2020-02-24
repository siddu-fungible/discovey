from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict, Counter
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.host.linux import Linux

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 2
            self.command_timeout = 5
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        # Declaring default values if not defined in config files
        if not hasattr(self, "dut_start_index"):
            self.dut_start_index = 0
        if not hasattr(self, "host_start_index"):
            self.host_start_index = 0
        if not hasattr(self, "update_workspace"):
            self.update_workspace = False
        if not hasattr(self, "update_deploy_script"):
            self.update_deploy_script = False

        # Using Parameters passed during execution, this will override global and config parameters
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = False
        if "f1_in_use" in job_inputs:
            self.f1_in_use = job_inputs["f1_in_use"]
        if "syslog" in job_inputs:
            self.syslog_level = job_inputs["syslog"]

        # Deploying of DUTs
        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        if self.testbed_type != "suite-based":
            self.testbed_config = fun_test.get_asset_manager().get_test_bed_spec(self.testbed_type)
            fun_test.log("{} Testbed Config: {}".format(self.testbed_type, self.testbed_config))
            self.fs_hosts_map = utils.parse_file_to_json(SCRIPTS_DIR + "/storage/inspur_fs_hosts_mapping.json")
            self.available_hosts = self.fs_hosts_map[self.testbed_type]["host_info"]
            self.full_dut_indexes = [int(i) for i in sorted(self.testbed_config["dut_info"].keys())]
            # Skipping DUTs not required for this test
            self.skip_dut_list = []
            for index in xrange(0, self.dut_start_index):
                self.skip_dut_list.append(index)
            for index in xrange(self.dut_start_index + self.num_duts, len(self.full_dut_indexes)):
                self.skip_dut_list.append(index)
            fun_test.log("DUTs that will be skipped: {}".format(self.skip_dut_list))
            self.available_dut_indexes = list(set(self.full_dut_indexes) - set(self.skip_dut_list))
            self.available_dut_indexes = [int(i) for i in self.available_dut_indexes]
            self.total_available_duts = len(self.available_dut_indexes)
            fun_test.log("Total Available Duts: {}".format(self.total_available_duts))
            self.topology_helper = TopologyHelper(spec=self.fs_hosts_map[self.testbed_type])
            # Making topology helper to skip DUTs in this list to initialise
            self.topology_helper.disable_duts(self.skip_dut_list)
        # Pulling reserved DUTs and Hosts and test bed specific configuration if script is submitted with testbed-type
        # suite-based
        elif self.testbed_type == "suite-based":
            self.topology_helper = TopologyHelper()
            self.available_dut_indexes = self.topology_helper.get_available_duts().keys()
            required_hosts_tmp = OrderedDict(self.topology_helper.get_available_hosts())
            self.required_hosts = OrderedDict()
            for index, host_name in enumerate(required_hosts_tmp):
                if index < self.num_hosts:
                    self.required_hosts[host_name] = required_hosts_tmp[host_name]
                else:
                    break
            self.testbed_config = self.topology_helper.spec
            self.total_available_duts = len(self.available_dut_indexes)

        fun_test.test_assert(expression=self.num_duts <= self.total_available_duts,
                             message="Testbed has enough DUTs")

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:

            # Code to collect csi_perf if it's set
            self.csi_perf_enabled = fun_test.get_job_environment_variable("csi_perf")
            fun_test.log("csi_perf_enabled is set as: {} for current run".format(self.csi_perf_enabled))
            if self.csi_perf_enabled:
                fun_test.log("testbed_config: {}".format(self.testbed_config))
                self.csi_f1_ip = \
                    self.testbed_config["dut_info"][str(self.available_dut_indexes[0])]["bond_interface_info"]["0"][
                        "0"][
                        "ip"].split('/')[0]
                fun_test.log("F1 ip used for csi_perf_test: {}".format(self.csi_f1_ip))
                self.perf_listener_host = self.topology_helper.get_available_perf_listener_hosts()
                fun_test.log("perf_listener_host used for current test: {}".format(self.perf_listener_host))
                for self.perf_listener_host_name, csi_perf_host_obj in self.perf_listener_host.iteritems():
                    perf_listner_test_interface = csi_perf_host_obj.get_test_interface(index=0)
                    self.perf_listener_ip = perf_listner_test_interface.ip.split('/')[0]
                    fun_test.log("csi perf listener host ip is: {}".format(self.perf_listener_ip))
                # adding csi perf bootargs if csi_perf is enabled
                #  TODO: Modifying bootargs only for F1_0 as csi_perf on F1_1 is not yet fully supported
                self.bootargs[0] += " --perf csi-local-ip={} csi-remote-ip={} pdtrace-hbm-size-kb={}".format(
                    self.csi_f1_ip, self.perf_listener_ip, self.csi_perf_pdtrace_hbm_size_kb)

            for i in range(len(self.bootargs)):
                self.bootargs[i] += " --mgmt"
                if self.disable_wu_watchdog:
                    self.bootargs[i] += " --disable-wu-watchdog"

            for dut_index in self.available_dut_indexes:
                self.topology_helper.set_dut_parameters(dut_index=dut_index,
                                                        f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                                       1: {"boot_args": self.bootargs[1]}})
            self.topology = self.topology_helper.deploy()
            fun_test.test_assert(self.topology, "Topology deployed")

            # Datetime required for daily Dashboard data filter
            self.db_log_time = get_data_collection_time(tag="ec_inspur_fs_teramark_single_f1")
            fun_test.log("Data collection time: {}".format(self.db_log_time))

            # Retrieving all Hosts list and filtering required hosts and forming required object lists out of it
            if self.testbed_type != "suite-based":
                hosts = self.topology.get_hosts()
                fun_test.log("Available hosts are: {}".format(hosts))
                required_host_index = []
                self.required_hosts = OrderedDict()

                for i in xrange(self.host_start_index, self.host_start_index + self.num_hosts):
                    required_host_index.append(i)
                fun_test.debug("Host index required for scripts: {}".format(required_host_index))
                for j, host_name in enumerate(sorted(hosts)):
                    if j in required_host_index:
                        self.required_hosts[host_name] = hosts[host_name]

            fun_test.log("Hosts that will be used for current test: {}".format(self.required_hosts.keys()))

            self.host_info = OrderedDict()
            self.hosts_test_interfaces = {}
            self.host_handles = {}
            self.host_ips = []
            self.host_numa_cpus = {}
            self.total_numa_cpus = {}
            for host_name, host_obj in self.required_hosts.items():
                if host_name not in self.host_info:
                    self.host_info[host_name] = {}
                    self.host_info[host_name]["ip"] = []
                # Retrieving host ips
                if host_name not in self.hosts_test_interfaces:
                    self.hosts_test_interfaces[host_name] = []
                test_interface = host_obj.get_test_interface(index=0)
                self.hosts_test_interfaces[host_name].append(test_interface)
                self.host_info[host_name]["test_interface"] = test_interface
                host_ip = self.hosts_test_interfaces[host_name][-1].ip.split('/')[0]
                self.host_ips.append(host_ip)
                self.host_info[host_name]["ip"].append(host_ip)
                fun_test.log("Host-IP: {}".format(host_ip))
                # Retrieving host handles
                host_instance = host_obj.get_instance()
                self.host_handles[host_ip] = host_instance
                self.host_info[host_name]["handle"] = host_instance

            """
            # Rebooting all the hosts in non-blocking mode before the test and getting NUMA cpus
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if self.override_numa_node["override"]:
                    host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
                    self.host_info[host_name]["host_numa_cpus"] = host_numa_cpus_filter[
                        self.override_numa_node["override_node"]]
                else:
                    self.host_info[host_name]["host_numa_cpus"] = fetch_numa_cpus(host_handle, self.ethernet_adapter)

                # Calculating the number of CPUs available in the given numa
                self.host_info[host_name]["total_numa_cpus"] = 0
                for cpu_group in self.host_info[host_name]["host_numa_cpus"].split(","):
                    cpu_range = cpu_group.split("-")
                    self.host_info[host_name]["total_numa_cpus"] += len(range(int(cpu_range[0]), int(cpu_range[1]))) + 1
                fun_test.log("Rebooting host: {}".format(host_name))
                host_handle.reboot(non_blocking=True)
            fun_test.log("Hosts info: {}".format(self.host_info))
            """

            # Getting FS, F1 and COMe objects, Storage Controller objects, F1 IPs
            # for all the DUTs going to be used in the test
            self.fs_obj = []
            self.fs_spec = []
            self.come_obj = []
            self.f1_obj = {}
            self.sc_obj = []
            self.f1_ips = []
            self.gateway_ips = []
            for curr_index, dut_index in enumerate(self.available_dut_indexes):
                self.fs_obj.append(self.topology.get_dut_instance(index=dut_index))
                self.fs_spec.append(self.topology.get_dut(index=dut_index))
                self.come_obj.append(self.fs_obj[curr_index].get_come())
                self.f1_obj[curr_index] = []
                for j in xrange(self.num_f1_per_fs):
                    self.f1_obj[curr_index].append(self.fs_obj[curr_index].get_f1(index=j))
                    self.sc_obj.append(self.f1_obj[curr_index][j].get_dpc_storage_controller())

            # Bringing up of FunCP docker container if it is needed
            self.funcp_obj = {}
            self.funcp_spec = {}
            for index in xrange(self.num_duts):
                self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
                self.funcp_spec[index] = self.funcp_obj[index].deploy_funcp_container(
                    update_deploy_script=self.update_deploy_script, update_workspace=self.update_workspace,
                    mode=self.funcp_mode)
                fun_test.test_assert(self.funcp_spec[index]["status"],
                                     "Starting FunCP docker container in DUT {}".format(index))
                self.funcp_spec[index]["container_names"].sort()
                for f1_index, container_name in enumerate(self.funcp_spec[index]["container_names"]):
                    bond_interfaces = self.fs_spec[index].get_bond_interfaces(f1_index=f1_index)
                    bond_name = "bond0"
                    bond_ip = bond_interfaces[0].ip
                    self.f1_ips.append(bond_ip.split('/')[0])
                    slave_interface_list = bond_interfaces[0].fpg_slaves
                    slave_interface_list = [self.fpg_int_prefix + str(i) for i in slave_interface_list]
                    self.funcp_obj[index].configure_bond_interface(container_name=container_name,
                                                                   name=bond_name,
                                                                   ip=bond_ip,
                                                                   slave_interface_list=slave_interface_list)
                    # Configuring route
                    route = self.fs_spec[index].spec["bond_interface_info"][str(f1_index)][str(0)]["route"][0]
                    cmd = "sudo ip route add {} via {} dev {}".format(route["network"], route["gateway"], bond_name)
                    route_add_status = self.funcp_obj[index].container_info[container_name].command(cmd)
                    fun_test.test_assert_expected(expected=0,
                                                  actual=self.funcp_obj[index].container_info[
                                                      container_name].exit_status(),
                                                  message="Configure Static route")

            # Forming shared variables for defined parameters
            fun_test.shared_variables["f1_in_use"] = self.f1_in_use
            fun_test.shared_variables["topology"] = self.topology
            fun_test.shared_variables["fs_obj"] = self.fs_obj
            fun_test.shared_variables["come_obj"] = self.come_obj
            fun_test.shared_variables["f1_obj"] = self.f1_obj
            fun_test.shared_variables["sc_obj"] = self.sc_obj
            fun_test.shared_variables["f1_ips"] = self.f1_ips
            fun_test.shared_variables["host_handles"] = self.host_handles
            fun_test.shared_variables["host_ips"] = self.host_ips
            fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
            fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
            fun_test.shared_variables["num_f1s"] = self.num_f1s
            fun_test.shared_variables["num_duts"] = self.num_duts
            fun_test.shared_variables["syslog_level"] = self.syslog_level
            fun_test.shared_variables["db_log_time"] = self.db_log_time
            fun_test.shared_variables["host_info"] = self.host_info
            fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
            if self.csi_perf_enabled:
                fun_test.shared_variables["perf_listener_host_name"] = self.perf_listener_host_name
                fun_test.shared_variables["perf_listener_ip"] = self.perf_listener_ip

            """
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                # Ensure all hosts are up after reboot
                fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                     message="Ensure Host {} is reachable after reboot".format(host_name))

                # Ensure required modules are loaded on host server, if not load it
                for module in self.load_modules:
                    module_check = host_handle.lsmod(module)
                    if not module_check:
                        host_handle.modprobe(module)
                        module_check = host_handle.lsmod(module)
                        fun_test.sleep("Loading {} module".format(module))
                    fun_test.simple_assert(module_check, "{} module is loaded".format(module))

            # Ensuring connectivity from Host to F1's
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                for index, ip in enumerate(self.f1_ips):
                    ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                    fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                         format(host_name, self.funcp_spec[0]["container_names"][index], ip))

            # Ensuring perf_host is able to ping F1 IP
            if self.csi_perf_enabled:
                # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
                csi_perf_host_instance = Linux(host_ip=csi_perf_host_obj.spec["host_ip"],
                                               ssh_username=csi_perf_host_obj.spec["ssh_username"],
                                               ssh_password=csi_perf_host_obj.spec["ssh_password"])
                ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                     format(self.perf_listener_host_name, self.csi_f1_ip))
            """
        elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["csr_replay"]:

            for i in range(len(self.bootargs)):
                self.bootargs[i] += " --csr-replay"
                if self.disable_wu_watchdog:
                    self.bootargs[i] += " --disable-wu-watchdog"

            self.topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                                   1: {"boot_args": self.bootargs[1]}})
            self.topology = self.topology_helper.deploy()
            fun_test.test_assert(self.topology, "Topology deployed")

            self.fs = self.topology.get_dut_instance(index=0)
            self.f1 = self.fs.get_f1(index=self.f1_in_use)
            self.db_log_time = get_data_collection_time()
            fun_test.log("Data collection time: {}".format(self.db_log_time))

            self.storage_controller = self.f1.get_dpc_storage_controller()

            # Fetching Linux host with test interface name defined
            fpg_connected_hosts = self.topology.get_host_instances_on_fpg_interfaces(dut_index=0,
                                                                                     f1_index=self.f1_in_use)
            for host_ip, host_info in fpg_connected_hosts.iteritems():
                if self.testbed_type == "fs-6" and host_ip != "poc-server-01":
                    continue
                if "test_interface_name" in host_info["host_obj"].extra_attributes:
                    self.end_host = host_info["host_obj"]
                    self.test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                    self.fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                    fun_test.log("Test Interface is connected to FPG Index: {}".format(self.fpg_inteface_index))
                    break
            else:
                fun_test.test_assert(False, "Host found with Test Interface")

            self.test_network = self.csr_network[str(self.fpg_inteface_index)]
            fun_test.shared_variables["end_host"] = self.end_host
            fun_test.shared_variables["topology"] = self.topology
            fun_test.shared_variables["fs"] = self.fs
            fun_test.shared_variables["f1_in_use"] = self.f1_in_use
            fun_test.shared_variables["test_network"] = self.test_network
            fun_test.shared_variables["syslog_level"] = self.syslog_level
            fun_test.shared_variables["db_log_time"] = self.db_log_time
            fun_test.shared_variables["storage_controller"] = self.storage_controller

            # Fetching NUMA node from Network host for mentioned Ethernet Adapter card
            if self.override_numa_node["override_node"]:
                self.numa_cpus_filter = self.end_host.lscpu(self.override_numa_node["override_node"])
                self.numa_cpus = self.numa_cpus_filter[self.override_numa_node["override_node"]]
            else:
                self.numa_cpus = fetch_numa_cpus(self.end_host, self.ethernet_adapter)

            # Calculating the number of CPUs available in the given numa
            self.total_numa_cpus = 0
            for cpu_group in self.numa_cpus.split(","):
                cpu_range = cpu_group.split("-")
                self.total_numa_cpus += len(range(int(cpu_range[0]), int(cpu_range[1]))) + 1

            fun_test.log("Total CPUs: {}".format(self.total_numa_cpus))
            fun_test.shared_variables["numa_cpus"] = self.numa_cpus
            fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus

            # Configuring Linux host
            host_up_status = self.end_host.reboot(timeout=self.command_timeout, max_wait_time=self.reboot_timeout,
                                                  reboot_initiated_wait_time=self.reboot_timeout)
            fun_test.test_assert(host_up_status, "End Host {} is up".format(self.end_host.host_ip))

            interface_ip_config = "ip addr add {} dev {}".format(self.test_network["test_interface_ip"],
                                                                 self.test_interface_name)
            interface_mac_config = "ip link set {} address {}".format(self.test_interface_name,
                                                                      self.test_network["test_interface_mac"])
            link_up_cmd = "ip link set {} up".format(self.test_interface_name)
            static_arp_cmd = "arp -s {} {}".format(self.test_network["test_net_route"]["gw"],
                                                   self.test_network["test_net_route"]["arp"])

            interface_ip_config_status = self.end_host.sudo_command(command=interface_ip_config,
                                                                    timeout=self.command_timeout)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message="Configuring test interface IP address")

            interface_mac_status = self.end_host.sudo_command(command=interface_mac_config,
                                                              timeout=self.command_timeout)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message="Assigning MAC to test interface")

            link_up_status = self.end_host.sudo_command(command=link_up_cmd, timeout=self.command_timeout)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message="Bringing up test link")

            interface_up_status = self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                                 action="up")
            fun_test.test_assert(interface_up_status, "Bringing up test interface")

            route_add_status = self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                                          gateway=self.test_network["test_net_route"]["gw"],
                                                          outbound_interface=self.test_interface_name,
                                                          timeout=self.command_timeout)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Adding route to F1")

            arp_add_status = self.end_host.sudo_command(command=static_arp_cmd, timeout=self.command_timeout)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message="Adding static ARP to F1 route")

            # Loading the nvme and nvme_tcp modules
            for module in self.load_modules:
                module_check = self.end_host.lsmod(module)
                if not module_check:
                    self.end_host.modprobe(module)
                    module_check = self.end_host.lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        fun_test.shared_variables["testbed_config"] = self.testbed_config

    def cleanup(self):

        come_reboot = False
        if fun_test.shared_variables["ec"]["setup_created"]:
            if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["enable_funcp"]:
                self.fs = self.fs_obj[0]
                self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
            elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["csr_replay"]:
                self.fs = fun_test.shared_variables["fs"]
                self.storage_controller = fun_test.shared_variables["storage_controller"]
            try:
                self.ec_info = fun_test.shared_variables["ec_info"]
                self.attach_transport = fun_test.shared_variables["attach_transport"]
                self.nvme_subsystem = fun_test.shared_variables["nvme_subsystem"]

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)
                self.storage_controller.disconnect()
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True


class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        # End of benchmarking json file parsing

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["attach_transport"] = self.attach_transport
        fun_test.shared_variables["nvme_subsystem"] = self.nvme_subsystem

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "num_volumes" in job_inputs:
            self.ec_info["num_volumes"] = job_inputs["num_volumes"]
        if "vol_size" in job_inputs:
            self.ec_info["capacity"] = job_inputs["vol_size"]

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            self.f1_in_use = fun_test.shared_variables["f1_in_use"]
            self.fs = fun_test.shared_variables["fs_obj"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1 = fun_test.shared_variables["f1_obj"][0][0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
            self.f1_ips = fun_test.shared_variables["f1_ips"][self.f1_in_use]
            self.host_info = fun_test.shared_variables["host_info"]
            self.num_f1s = fun_test.shared_variables["num_f1s"]
            self.test_network = {}
            self.test_network["f1_loopback_ip"] = self.f1_ips
            self.num_duts = fun_test.shared_variables["num_duts"]
            self.num_hosts = len(self.host_info)
            self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
            if self.csi_perf_enabled:
                self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
                self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["csr_replay"]:
            self.fs = fun_test.shared_variables["fs"]
            self.end_host = fun_test.shared_variables["end_host"]
            self.test_network = fun_test.shared_variables["test_network"]
            self.f1_in_use = fun_test.shared_variables["f1_in_use"]
            self.storage_controller = fun_test.shared_variables["storage_controller"]
            self.numa_cpus = fun_test.shared_variables["numa_cpus"]
            self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"]
            self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
            fun_test.shared_variables["remote_ip"] = self.remote_ip

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ec_info"] = self.ec_info

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                          command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            # Preparing the volume details list containing the list of ditionaries where each dictionary has the
            # details of an EC volume
            self.vol_details = []
            for num in range(self.ec_info["num_volumes"]):
                vol_group = {}
                vol_group[self.ec_info["volume_types"]["ndata"]] = self.ec_info["uuids"][num]["blt"]
                vol_group[self.ec_info["volume_types"]["ec"]] = self.ec_info["uuids"][num]["ec"]
                vol_group[self.ec_info["volume_types"]["jvol"]] = [self.ec_info["uuids"][num]["jvol"]]
                vol_group[self.ec_info["volume_types"]["lsv"]] = self.ec_info["uuids"][num]["lsv"]
                self.vol_details.append(vol_group)
            fun_test.log("vol_details is: {}".format(self.vol_details))
            fun_test.shared_variables["vol_details"] = self.vol_details

        for i in range(self.iteration):
            try:
                vol_stats = self.storage_controller.peek(
                    props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                fun_test.test_assert(vol_stats["data"], "Volume Stats - Iteration {}".format(i))
                fun_test.log("\nIteration {} - Volume stats:\n {}".format(i, vol_stats["data"]))
                per_vp_result = self.storage_controller.peek(props_tree="stats/per_vp", legacy=False, chunk=8192,
                                                             command_duration=self.command_timeout)
                fun_test.test_assert(per_vp_result["data"], "Per VP Stats - Iteration {}".format(i))
                fun_test.log("\nIteration {} - Per VP Stats:\n {}".format(i, per_vp_result["data"]))
            except Exception as ex:
                try:
                    echo_status = self.storage_controller.json_execute(verb="echo", data=["hello"], command_duration=10)
                    while echo_status["data"] != "hello":
                        fun_test.sleep("to recover from error", seconds=1)
                        echo_status = self.storage_controller.json_execute(verb="echo", data=["hello"],
                                                                           command_duration=10)
                    fun_test.sleep("to recover from error", seconds=1)
                    echo_status = self.storage_controller.json_execute(verb="echo", data=["hello"], command_duration=10)
                except Exception as ex:
                    pass

    def run(self):
        pass

    def cleanup(self):
        pass


class TestDpcsh(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test to check the consistency of dpcsh request and response",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Run "peek storage/volumes" for N iterations and ensure all for all the N requests the dpcsh proxy server
        returned the proper result
        """)

    def setup(self):
        super(TestDpcsh, self).setup()

    def run(self):
        super(TestDpcsh, self).run()

    def cleanup(self):
        super(TestDpcsh, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(TestDpcsh())
    ecscript.run()
