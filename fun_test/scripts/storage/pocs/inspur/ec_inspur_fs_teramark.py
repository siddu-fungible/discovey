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
            self.required_hosts = self.topology_helper.get_available_hosts()
            self.testbed_config = self.topology_helper.spec
            self.total_available_duts = len(self.available_dut_indexes)

        fun_test.test_assert(expression=self.num_duts <= self.total_available_duts, message="Testbed has enough DUTs")

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

            self.hosts_test_interfaces = {}
            self.host_handles = {}
            self.host_ips = []
            self.host_numa_cpus = {}
            self.total_numa_cpus = {}
            for host_name, host_obj in self.required_hosts.items():
                # Retrieving host ips
                if host_name not in self.hosts_test_interfaces:
                    self.hosts_test_interfaces[host_name] = []
                test_interface = host_obj.get_test_interface(index=0)
                self.hosts_test_interfaces[host_name].append(test_interface)
                host_ip = self.hosts_test_interfaces[host_name][-1].ip.split('/')[0]
                self.host_ips.append(host_ip)
                fun_test.log("Host-IP: {}".format(host_ip))
                # Retrieving host handles
                host_instance = host_obj.get_instance()
                self.host_handles[host_ip] = host_instance

            # Rebooting all the hosts in non-blocking mode before the test and getting NUMA cpus
            for key in self.host_handles:
                if self.override_numa_node["override"]:
                    self.host_numa_cpus_filter = self.host_handles[key].lscpu(self.override_numa_node["override_node"])
                    self.host_numa_cpus[key] = self.host_numa_cpus_filter[self.override_numa_node["override_node"]]
                else:
                    self.host_numa_cpus[key] = fetch_numa_cpus(self.host_handles[key], self.ethernet_adapter)

                # Calculating the number of CPUs available in the given numa
                self.total_numa_cpus[key] = 0
                for cpu_group in self.host_numa_cpus[key].split(","):
                    cpu_range = cpu_group.split("-")
                    self.total_numa_cpus[key] += len(range(int(cpu_range[0]), int(cpu_range[1]))) + 1
                fun_test.log("Rebooting host: {}".format(key))
                self.host_handles[key].reboot(non_blocking=True)
            fun_test.log("NUMA CPU for Host: {}".format(self.host_numa_cpus))
            fun_test.log("Total CPUs: {}".format(self.total_numa_cpus))

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

            for key in self.host_handles:
                # Ensure all hosts are up after reboot
                fun_test.test_assert(self.host_handles[key].ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                     message="Ensure Host {} is reachable after reboot".format(key))

                # TODO: enable after mpstat check is added
                """
                # Check and install systat package
                install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
                fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
                """
                # Ensure required modules are loaded on host server, if not load it
                for module in self.load_modules:
                    module_check = self.host_handles[key].lsmod(module)
                    if not module_check:
                        self.host_handles[key].modprobe(module)
                        module_check = self.host_handles[key].lsmod(module)
                        fun_test.sleep("Loading {} module".format(module))
                    fun_test.simple_assert(module_check, "{} module is loaded".format(module))

            # Ensuring connectivity from Host to F1's
            for key in self.host_handles:
                for index, ip in enumerate(self.f1_ips):
                    ping_status = self.host_handles[key].ping(dst=ip)
                    fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                         format(key, self.funcp_spec[0]["container_names"][index], ip))

        elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["csr_replay"]:

            for i in range(len(self.bootargs)):
                self.bootargs[i] += " --csr-replay"
                if self.disable_wu_watchdog:
                    self.bootargs[i] += " --disable-wu-watchdog"

            topology_helper = TopologyHelper()
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                              1: {"boot_args": self.bootargs[1]}})
            self.topology = topology_helper.deploy()
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
                    self.come_obj[index].command("sudo rmmod funeth", timeout=180)
                    fun_test.test_assert_expected(expected=0, actual=self.come_obj[index].exit_status(),
                                                  message="funeth module is unloaded")
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True
        '''
        # disabling COMe reboot in cleanup section as, setup bring-up handles it through COMe power-cycle
        try:
            if come_reboot:
                self.fs.fpga_initialize()
                fun_test.log("Unexpected exit: Rebooting COMe to ensure next script execution won't ged affected")
                self.fs.come_reset(max_wait_time=self.reboot_timeout)
        except Exception as ex:
            fun_test.critical(str(ex))
        '''
        # fun_test.sleep("Allowing buffer time before clean-up", 30)
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

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "warmup_bs" in job_inputs:
            self.warm_up_fio_cmd_args["bs"] = job_inputs["warmup_bs"]
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["attach_transport"] = self.attach_transport

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            self.fs = fun_test.shared_variables["fs_obj"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1 = fun_test.shared_variables["f1_obj"][0][0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            self.f1_ips = fun_test.shared_variables["f1_ips"][0]
            self.host_handles = fun_test.shared_variables["host_handles"]
            self.host_ips = fun_test.shared_variables["host_ips"]
            self.end_host = self.host_handles[self.host_ips[0]]
            self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
            self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
            self.num_f1s = fun_test.shared_variables["num_f1s"]
            self.test_network = {}
            self.test_network["f1_loopback_ip"] = self.f1_ips
            self.remote_ip = self.host_ips[0]
            fun_test.shared_variables["remote_ip"] = self.remote_ip
            self.num_duts = fun_test.shared_variables["num_duts"]
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
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                       transport=self.attach_transport,
                                                                       remote_ip=self.remote_ip,
                                                                       nqn=self.nvme_subsystem,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create Storage Controller for {} with controller uuid {} on DUT".
                                 format(self.attach_transport, self.ctrlr_uuid))

            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid, ns_id=num + 1, vol_uuid=self.ec_info["attach_uuid"][num],
                    command_duration=self.command_timeout)
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

            if not fun_test.shared_variables["ec"]["nvme_connect"]:
                # Checking nvme-connect status
                if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                        self.testbed_config["workarounds"]["enable_funcp"]:
                    if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem, self.remote_ip)
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem, str(self.io_queues), self.remote_ip)
                else:
                    if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem)
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem, str(self.io_queues))

                nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
                fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
                fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                              message="NVME Connect Status")

                lsblk_output = self.end_host.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")

                # Checking that the above created BLT volume is visible to the end host
                self.nvme_block_device_list = []
                for num in xrange(self.ec_info["num_volumes"]):
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(num + 1)
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(num + 1)
                            self.nvme_block_device_list.append(self.nvme_block_device)
                            self.volume_name = self.nvme_block_device.replace("/dev/", "")
                            fun_test.test_assert_expected(expected=self.volume_name,
                                                          actual=lsblk_output[volume_name]["name"],
                                                          message="{} device available".format(self.volume_name))
                            break
                    else:
                        fun_test.test_assert(False, "{} device available".format(self.volume_name))
                    fun_test.log("NVMe Block Device/s: {}".format(self.nvme_block_device_list))

                fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
                fun_test.shared_variables["volume_name"] = self.volume_name
                fun_test.shared_variables["ec"]["nvme_connect"] = True

                self.fio_filename = ":".join(self.nvme_block_device_list)
                fun_test.shared_variables["self.fio_filename"] = self.fio_filename

            # Executing the FIO command to fill the volume to it's capacity
            if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
                fun_test.log("Executing the FIO command to perform sequential write to volume")
                fio_output = self.end_host.pcie_fio(filename=self.fio_filename, cpus_allowed=self.numa_cpus,
                                                    **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.test_assert(fio_output, "Pre-populating the volume")

                fun_test.shared_variables["ec"]["warmup_io_completed"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
            self.fio_filename = fun_test.shared_variables["self.fio_filename"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

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

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}

        start_mpstat = True

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = {}
            fio_output[iodepth] = {}
            fio_cmd_args = {}

            # Deciding the numjobs and IO depth together will provide the target IO depth based on the available cores
            if iodepth <= self.total_numa_cpus:
                fio_num_jobs = iodepth
                fio_iodepth = 1
            else:
                io_factor = 2
                while True:
                    if (iodepth / io_factor) <= self.total_numa_cpus:
                        fio_num_jobs = iodepth / io_factor
                        fio_iodepth = io_factor
                        break
                    else:
                        io_factor += 1

            fio_job_name = self.fio_job_name + "_" + str(int(fio_iodepth) * int(fio_num_jobs))
            fun_test.log("fio_job_name used for current iteration: {}".format(fio_job_name))

            if "multiple_jobs" in self.fio_cmd_args:
                num_jobs = self.fio_cmd_args["multiple_jobs"].count("name")
                fio_num_jobs = fio_num_jobs / num_jobs
            else:
                num_jobs = 1

            fio_result[iodepth] = True
            row_data_dict = {}
            row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_num_jobs)
            size = self.ec_info["capacity"] / (1024 ** 3)
            row_data_dict["size"] = str(size) + "G"

            fun_test.sleep("Waiting in between iterations", self.iter_interval)

            # Collecting mpstat during IO
            mpstat_cpu_list = self.mpstat_args["cpu_list"]  # To collect mpstat for all CPU's: recommended
            # mpstat_cpu_list = self.numa_cpus  # To collect mpstat for NUMA CPU's only
            fun_test.log("Collecting mpstat")
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
                    start_mpstat = False
            else:
                start_mpstat = False

            if start_mpstat:
                mpstat_pid = self.end_host.mpstat(cpu_list=mpstat_cpu_list, output_file=self.mpstat_args["output_file"],
                                                  interval=self.mpstat_args["interval"], count=int(mpstat_count))
            else:
                fun_test.critical("Not starting the mpstat because of lack of interval and count details")

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
                         format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * num_jobs))

            fio_output[iodepth] = {}
            if "multiple_jobs" in self.fio_cmd_args:
                fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].format(self.numa_cpus, fio_num_jobs,
                                                                                          fio_iodepth)
                fio_output[iodepth] = self.end_host.pcie_fio(filename=self.fio_filename,
                                                             timeout=self.fio_cmd_args["timeout"], **fio_cmd_args)
            else:
                fio_output[iodepth] = self.end_host.pcie_fio(filename=self.fio_filename, numjobs=fio_num_jobs,
                                                             iodepth=fio_iodepth, name=fio_job_name,
                                                             cpus_allowed=self.numa_cpus, **self.fio_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output[iodepth]))
            fun_test.test_assert(fio_output[iodepth], "FIO {} test with the Block Size {} IO depth {} and Numjobs {}"
                                 .format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * num_jobs    ))

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
            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Inspur Performance Test", test_method, *row_data_list)

            # Checking if mpstat process is still running
            if start_mpstat:
                mpstat_pid_check = self.end_host.get_process_id("mpstat")
                if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid):
                    self.end_host.kill_process(process_id=mpstat_pid)
                self.end_host.read_file(file_name=self.mpstat_args["output_file"])

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
                              summary="Inspur TC 8.11.1: 8k data block random read/write IOPS performance of EC volume",
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
                                      "of EC volume",
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
                              summary="Inspur TC 8.11.3: Integrated model read/write IOPS performance of EC volume",
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
                              summary="Inspur TC 8.11.4: OLTP Model read/read IOPS performance of EC volume",
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
                              summary="Inspur TC 8.11.5: OLAP Model read/write IOPS performance of EC volume",
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
    # ecscript.add_test_case(RandReadWrite8kBlocks())
    ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    ecscript.add_test_case(MixedRandReadWriteIOPS())
    ecscript.add_test_case(OLTPModelReadWriteIOPS())
    ecscript.add_test_case(OLAPModelReadWriteIOPS())
    ecscript.run()
