from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volumes = fun_test.shared_variables["num_volumes"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volumes, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


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
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = True

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
            self.full_dut_indexes = self.testbed_config["dut_info"]
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
            self.required_hosts = OrderedDict(self.topology_helper.get_available_hosts())
            self.testbed_config = self.topology_helper.spec
            self.total_available_duts = len(self.available_dut_indexes)

        fun_test.test_assert(expression=self.num_duts <= self.total_available_duts,
                             message="Testbed has enough DUTs")

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
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

            self.host_info = {}
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
                host_ip = self.hosts_test_interfaces[host_name][-1].ip.split('/')[0]
                self.host_ips.append(host_ip)
                self.host_info[host_name]["ip"].append(host_ip)
                fun_test.log("Host-IP: {}".format(host_ip))
                # Retrieving host handles
                host_instance = host_obj.get_instance()
                self.host_handles[host_ip] = host_instance
                self.host_info[host_name]["handle"] = host_instance

            # Rebooting all the hosts in non-blocking mode before the test and getting NUMA cpus
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if self.override_numa_node["override"]:
                    host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
                    # self.host_numa_cpus[key] = host_numa_cpus_filter[self.override_numa_node["override_node"]]
                    self.host_info[host_name]["host_numa_cpus"] = host_numa_cpus_filter[self.override_numa_node["override_node"]]
                else:
                    # self.host_numa_cpus[key] = fetch_numa_cpus(self.host_handles[key], self.ethernet_adapter)
                    self.host_info[host_name]["host_numa_cpus"] = fetch_numa_cpus(host_handle, self.ethernet_adapter)

                # Calculating the number of CPUs available in the given numa
                """self.total_numa_cpus[key] = 0
                for cpu_group in self.host_numa_cpus[key].split(","):
                    cpu_range = cpu_group.split("-")
                    self.total_numa_cpus[key] += len(range(int(cpu_range[0]), int(cpu_range[1]))) + 1
                fun_test.log("Rebooting host: {}".format(key))
                self.host_handles[key].reboot(non_blocking=True)"""
                self.host_info[host_name]["total_numa_cpus"] = 0
                for cpu_group in self.host_info[host_name]["host_numa_cpus"].split(","):
                    cpu_range = cpu_group.split("-")
                    self.host_info[host_name]["total_numa_cpus"] += len(range(int(cpu_range[0]), int(cpu_range[1]))) + 1
                fun_test.log("Rebooting host: {}".format(host_name))
                host_handle.reboot(non_blocking=True)
            # fun_test.log("NUMA CPU for Host: {}".format(self.host_numa_cpus))
            # fun_test.log("Total CPUs: {}".format(self.total_numa_cpus))
            fun_test.log("Hosts info: {}".format(self.host_info))

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
                    # self.funcp_obj[index].container_info[container_name].command("hostname")
                    cmd = "sudo ip route add {} via {} dev {}".format(route["network"], route["gateway"], bond_name)
                    route_add_status = self.funcp_obj[index].container_info[container_name].command(cmd)
                    fun_test.test_assert_expected(expected=0,
                                                  actual=self.funcp_obj[index].container_info[
                                                      container_name].exit_status(),
                                                  message="Configure Static route")

            # Forming shared variables for defined parameters
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

            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                # Ensure all hosts are up after reboot
                fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                     message="Ensure Host {} is reachable after reboot".format(host_name))

                # TODO: enable after mpstat check is added
                """
                # Check and install systat package
                install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
                fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
                """
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
            fpg_connected_hosts = self.topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
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
                self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["csr_replay"]:
                self.fs = fun_test.shared_variables["fs"]
                self.storage_controller = fun_test.shared_variables["storage_controller"]
            try:
                self.ec_info = fun_test.shared_variables["ec_info"]
                self.remote_ip = fun_test.shared_variables["remote_ip"]
                self.attach_transport = fun_test.shared_variables["attach_transport"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                # Detaching all the EC/LS volumes to the external server
                """for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid, ns_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)

                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Storage Controller Delete")"""
                self.storage_controller.disconnect()
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            try:
                for index in xrange(self.num_duts):
                    stop_containers = self.funcp_obj[index].stop_container()
                    fun_test.test_assert_expected(expected=True, actual=stop_containers,
                                                  message="Docker containers are stopped")
                    self.come_obj[index].command("sudo rmmod funeth")
                    fun_test.test_assert_expected(expected=0, actual=self.come_obj[index].exit_status(),
                                                  message="funeth module is unloaded")
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True
        try:
            if come_reboot:
                self.fs.fpga_initialize()
                fun_test.log("Unexpected exit: Rebooting COMe to ensure next script execution won't ged affected")
                self.fs.come_reset(max_wait_time=self.reboot_timeout)
        except Exception as ex:
            fun_test.critical(str(ex))

        self.topology.cleanup()


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
            self.fs = fun_test.shared_variables["fs_obj"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1 = fun_test.shared_variables["f1_obj"][0][0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            self.f1_ips = fun_test.shared_variables["f1_ips"][0]
            self.host_info = fun_test.shared_variables["host_info"]
            """
            self.host_handles = fun_test.shared_variables["host_handles"]
            self.host_ips = fun_test.shared_variables["host_ips"]
            self.end_host = self.host_handles[self.host_ips[0]]
            self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
            self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
            self.remote_ip = self.host_ips[0]
            fun_test.shared_variables["remote_ip"] = self.remote_ip
            """
            self.num_f1s = fun_test.shared_variables["num_f1s"]
            self.test_network = {}
            self.test_network["f1_loopback_ip"] = self.f1_ips
            self.num_duts = fun_test.shared_variables["num_duts"]
            self.num_hosts = len(self.host_info)
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

            # Attaching/Exporting all the EC/LS volumes to the external server
            self.ctrlr_uuid = []
            for host_name in self.host_info:
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                           transport=self.attach_transport,
                                                                           remote_ip=self.host_info[host_name]["ip"][0],
                                                                           nqn=self.nvme_subsystem,
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Create Storage Controller for {} with controller uuid {} on DUT".
                                     format(self.attach_transport, self.ctrlr_uuid[-1]))

            for num in xrange(self.ec_info["num_volumes"]):
                curr_ctrlr_index = num % self.num_hosts
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[curr_ctrlr_index], ns_id=num + 1,
                    vol_uuid=self.ec_info["attach_uuid"][num], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

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

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

            fun_test.shared_variables["fio"] = {}
            for host_name in self.host_info:
                fun_test.shared_variables["ec"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]
                if not fun_test.shared_variables["ec"]["nvme_connect"]:
                    # Checking nvme-connect status
                    if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                            self.testbed_config["workarounds"]["enable_funcp"]:
                        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem,
                                       self.host_info[host_name]["ip"][0])
                        else:
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem, str(self.io_queues),
                                       self.host_info[host_name]["ip"][0])
                    else:
                        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem)
                        else:
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem, str(self.io_queues))

                    nvme_connect_status = host_handle.sudo_command(command=nvme_connect_cmd,
                                                                   timeout=self.command_timeout)
                    fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
                    fun_test.test_assert_expected(expected=0, actual=host_handle.exit_status(),
                                                  message="{} - NVME Connect Status".format(host_name))

                    lsblk_output = host_handle.lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")

                    # Checking that the above created BLT volume is visible to the end host
                    self.host_info[host_name]["nvme_block_device_list"] = []
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                                     str(match.group(2))
                            self.host_info[host_name]["nvme_block_device_list"].append(self.nvme_block_device)
                            fun_test.log("NVMe Block Device/s: {}".
                                         format(self.host_info[host_name]["nvme_block_device_list"]))

                    fun_test.test_assert_expected(expected=self.ec_info["num_volumes"] / self.num_hosts,
                                                  actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                                  message="Expected NVMe devices are available")
                    fun_test.shared_variables["ec"][host_name]["nvme_connect"] = True

                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["fio_filename"] = \
                        ":".join(self.host_info[host_name]["nvme_block_device_list"])
                    fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

            # Executing the FIO command to fill the volume to it's capacity
            if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
                host_clone = {}
                warmup_thread_id = {}
                for index, host_name in enumerate(self.host_info):
                    wait_time = self.num_hosts - index
                    host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                    warmup_thread_id[index] = fun_test.execute_thread_after(
                        time_in_seconds=wait_time, func=fio_parser, arg1=host_clone[host_name], host_index=index,
                        filename=self.host_info[host_name]["fio_filename"],
                        cpus_allowed=self.host_info[host_name]["host_numa_cpus"], **self.warm_up_fio_cmd_args)

                    fun_test.log("Started FIO command to perform sequential write on {}".format(host_name))
                    fun_test.sleep("to start next thread", 1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for index, host_name in enumerate(self.host_info):
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=warmup_thread_id[index])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][index])
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Fio threaded warmup test")
                        fun_test.shared_variables["ec"][host_name]["warmup"] = True
                except Exception as ex:
                    fun_test.critical(str(ex))

                fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                               self.iter_interval)
                fun_test.shared_variables["ec"]["warmup_io_completed"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        # Checking whether the job's inputs argument is having the list of io_depths to be used in this test.
        # If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_iodepth = job_inputs["io_depth"]

        if not isinstance(self.fio_iodepth, list):
            self.fio_iodepth = [self.fio_iodepth]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}

        start_stats = True

        fio_job_args = ""
        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            fio_cmd_args = {}

            row_data_dict = {}
            size = (self.ec_info["capacity"] * self.ec_info["num_volumes"]) / (1024 ** 3)
            row_data_dict["size"] = str(size) + "G"

            # Deciding whether the fio command has to run for the entire volume size or for a certain period of time,
            # based on if the current IO depth is in self.full_run_iodepth
            if iodepth not in self.full_run_iodepth:
                if "runtime" not in self.fio_cmd_args["multiple_jobs"]:
                    self.fio_cmd_args["multiple_jobs"] += " --time_based --runtime={}".format(self.fio_runtime)
                    self.fio_cmd_args["timeout"] = self.fio_run_timeout
            else:
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--runtime=\d+", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--time_based", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["timeout"] = self.fio_size_timeout

            # Computing the interval and duration that the mpstat/vp_util needs to be collected
            if "runtime" not in self.fio_cmd_args:
                mpstat_count = self.fio_cmd_args["timeout"] / self.mpstat_args["interval"]
            elif "runtime" in self.fio_cmd_args and "ramp_time" in self.fio_cmd_args:
                mpstat_count = ((self.fio_cmd_args["runtime"] + self.fio_cmd_args["ramp_time"]) /
                                self.mpstat_args["interval"])
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--ramp_time=(\d+).*--runtime=(\d+)|--runtime=(\d+).*--ramp_time=(\d+)",
                                  self.fio_cmd_args["multiple_jobs"])
                if match:
                    if match.group(1) != None:
                        ramp_time = match.group(1)
                    if match.group(2) != None:
                        runtime = match.group(2)
                    if match.group(3) != None:
                        runtime = match.group(3)
                    if match.group(4) != None:
                        ramp_time = match.group(4)
                    mpstat_count = (int(runtime) + int(ramp_time)) / self.mpstat_args["interval"]
                else:
                    start_stats = False
            else:
                start_stats = False

            if start_stats:
                vp_util_post_fix_name = "vp_util_iodepth_{}.txt".format(row_data_dict["iodepth"])
                vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_post_fix_name)
                warmup_thread_id = fun_test.execute_thread_after(time_in_seconds=1, func=collect_vp_utils_stats,
                                                                 storage_controller=self.storage_controller,
                                                                 output_file=vp_util_artifact_file,
                                                                 interval=self.vp_util_args["interval"],
                                                                 count=int(mpstat_count))
            else:
                fun_test.critical("Not starting the vp_utils stats collection because of lack of interval and count "
                                  "details")

            for index, host_name in enumerate(self.host_info):
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                total_numa_cpus = self.host_info[host_name]["total_numa_cpus"]
                fio_num_jobs = len(nvme_block_device_list)

                for index, volume_name in enumerate(nvme_block_device_list):
                    fio_job_args += " --name=job{} --filename={}".format(index, volume_name)

                if "multiple_jobs" in self.fio_cmd_args and self.fio_cmd_args["multiple_jobs"].count("name") > 0:
                    global_num_jobs = self.fio_cmd_args["multiple_jobs"].count("name")
                    fio_num_jobs = fio_num_jobs / global_num_jobs
                else:
                    if iodepth <= total_numa_cpus:
                        global_num_jobs = iodepth / len(nvme_block_device_list)
                        fio_iodepth = 1
                    else:
                        io_factor = 2
                        while True:
                            if (iodepth / io_factor) <= self.total_numa_cpus:
                                global_num_jobs = (iodepth / len(nvme_block_device_list)) / io_factor
                                fio_iodepth = io_factor
                                break
                            else:
                                io_factor += 1

                row_data_dict["iodepth"] = int(fio_iodepth) * int(global_num_jobs) * int(fio_num_jobs)
                fun_test.sleep("Waiting in between iterations", self.iter_interval)

                # Collecting mpstat during IO
                mpstat_cpu_list = self.mpstat_args["cpu_list"]  # To collect mpstat for all CPU's: recommended
                fun_test.log("Collecting mpstat")
                if start_stats:
                    mpstat_post_fix_name = "mpstat_iodepth_{}.txt".format(row_data_dict["iodepth"])
                    vp_util_post_fix_name = "vp_util_iodepth_{}.txt".format(row_data_dict["iodepth"])
                    mpstat_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=mpstat_post_fix_name)
                    vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_post_fix_name)

                    mpstat_pid = self.end_host.mpstat(cpu_list=mpstat_cpu_list, output_file=self.mpstat_args["output_file"],
                                                      interval=self.mpstat_args["interval"], count=int(mpstat_count))
                    thread_id = fun_test.execute_thread_after(time_in_seconds=1, func=collect_vp_utils_stats,
                                                              storage_controller=self.storage_controller,
                                                              output_file=vp_util_artifact_file,
                                                              interval=self.vp_util_args["interval"],
                                                              count=int(mpstat_count))
                    # collect_vp_utils_stats(self.storage_controller, vp_util_artifact_file,
                    #                        interval=30, count=4)
                else:
                    fun_test.critical("Not starting the stats collection because of lack of interval and count details")

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                if "bs" in self.fio_cmd_args:
                    fio_block_size = self.fio_cmd_args["bs"]
                else:
                    fio_block_size = "Mixed"

                if "rw" in self.fio_cmd_args:
                    row_data_dict["mode"] = self.fio_cmd_args["rw"]
                else:
                    row_data_dict["mode"] = "Combined"

                row_data_dict["block_size"] = fio_block_size

                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * global_num_jobs))
                if self.ec_info["num_volumes"] != 1:
                    fio_job_name = "{}_iodepth_{}_vol_{}".format(self.fio_job_name, row_data_dict["iodepth"],
                                                                 self.ec_info["num_volumes"])
                else:
                    fio_job_name = "{}_{}".format(self.fio_job_name, row_data_dict["iodepth"])

                fun_test.log("fio_job_name used for current iteration: {}".format(fio_job_name))
                fio_output[iodepth] = {}
                try:
                    if "multiple_jobs" in self.fio_cmd_args:
                        fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].format(
                            self.numa_cpus, global_num_jobs, fio_iodepth, self.ec_info["capacity"] / global_num_jobs)
                        fio_cmd_args["multiple_jobs"] += fio_job_args
                        fio_output[iodepth] = self.end_host.pcie_fio(filename=self.fio_filename,
                                                                     timeout=self.fio_cmd_args["timeout"], **fio_cmd_args)
                    else:
                        fio_output[iodepth] = self.end_host.pcie_fio(filename=self.fio_filename, numjobs=fio_num_jobs,
                                                                     iodepth=fio_iodepth, name=fio_job_name,
                                                                     cpus_allowed=self.numa_cpus, **self.fio_cmd_args)
                except Exception as ex:
                    fun_test.critical(str(ex))
                    # Checking whether the vp_util stats collection thread is still running...If so stopping it...
                    if fun_test.fun_test_threads[thread_id]["thread"].is_alive():
                        fun_test.critical("VP utilization stats collection thread is still running...Stopping it now")
                        fun_test.fun_test_threads[thread_id]["thread"]._Thread__stop()

                fun_test.log("FIO Command Output:\n{}".format(fio_output[iodepth]))
                fun_test.test_assert(fio_output[iodepth],
                                     "FIO {} test with the Block Size {} IO depth {} and Numjobs {}"
                                     .format(row_data_dict["mode"], fio_block_size, fio_iodepth,
                                             fio_num_jobs * global_num_jobs))

                for op, stats in fio_output[iodepth].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[iodepth][op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[iodepth][op][field] = int(round(value / 1000))
                        if field == "latency":
                            fio_output[iodepth][op][field] = int(round(value))
                        row_data_dict[op + field] = fio_output[iodepth][op][field]

                if not fio_output[iodepth]:
                    fio_result[iodepth] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                row_data_dict["fio_job_name"] = fio_job_name

            # Building the table raw for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)
            post_results("Inspur Performance Test", test_method, *row_data_list)

            # Checking if mpstat process is still running...If so killing it...
            mpstat_pid_check = self.end_host.get_process_id("mpstat")
            if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid):
                self.end_host.kill_process(process_id=mpstat_pid)
            # Saving the mpstat output to the mpstat_artifact_file file
            """mpstat_data = self.end_host.read_file(file_name=self.mpstat_args["output_file"])
            with open(mpstat_artifact_file, 'a') as f:
                f.writelines(mpstat_data)"""
            fun_test.scp(source_port=self.end_host.ssh_port, source_username=self.end_host.ssh_username,
                         source_password=self.end_host.ssh_password, source_ip=self.end_host.host_ip,
                         source_file_path=self.mpstat_args["output_file"], target_file_path=mpstat_artifact_file)
            fun_test.add_auxillary_file(description="Host CPU Usage - IO depth {}".format(row_data_dict["iodepth"]),
                                        filename=mpstat_artifact_file)

            # Checking whether the vp_util stats collection thread is still running...If so stopping it...
            if fun_test.fun_test_threads[thread_id]["thread"].is_alive():
                fun_test.critical("VP utilization stats collection thread is still running...Stopping it now")
                fun_test.fun_test_threads[thread_id]["thread"]._Thread__stop()
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
            fun_test.add_auxillary_file(description="F1 VP Utilization - IO depth {}".format(row_data_dict["iodepth"]),
                                        filename=vp_util_artifact_file)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for iodepth in self.fio_iodepth:
            if not fio_result[iodepth]:
                test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class RandReadWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1: 8k data block random read/write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RandReadWrite8kBlocks, self).setup()

    def run(self):
        super(RandReadWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocks, self).cleanup()


class SequentialReadWrite1024kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.11.2: 1024k data block sequential write IOPS performance"
                                      "of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 1024k transfer size Sequential write IOPS
        """)

    def setup(self):
        super(SequentialReadWrite1024kBlocks, self).setup()

    def run(self):
        super(SequentialReadWrite1024kBlocks, self).run()

    def cleanup(self):
        super(SequentialReadWrite1024kBlocks, self).cleanup()


class MixedRandReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Inspur TC 8.11.3: Integrated model read/write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for Integrated Model read/write IOPS
        """)

    def setup(self):
        super(MixedRandReadWriteIOPS, self).setup()

    def run(self):
        super(MixedRandReadWriteIOPS, self).run()

    def cleanup(self):
        super(MixedRandReadWriteIOPS, self).cleanup()


class OLTPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Inspur TC 8.11.4: OLTP Model read/read IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLTP model read/write IOPS
        """)

    def setup(self):
        super(OLTPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLTPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLTPModelReadWriteIOPS, self).cleanup()


class OLAPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Inspur TC 8.11.5: OLAP Model read/write IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLAP model Random read/write IOPS
        """)

    def setup(self):
        super(OLAPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLAPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLAPModelReadWriteIOPS, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    # ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    # ecscript.add_test_case(MixedRandReadWriteIOPS())
    # ecscript.add_test_case(OLTPModelReadWriteIOPS())
    # ecscript.add_test_case(OLAPModelReadWri`teIOPS())
    ecscript.run()
