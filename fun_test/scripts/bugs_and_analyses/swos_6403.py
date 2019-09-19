from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from lib.system.utils import *
from lib.host.storage_controller import *
from collections import OrderedDict, Counter
from math import ceil


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


class WorkloadTriggerTestScript(FunTestScript):
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
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]

        # Deploying of DUTs
        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        if self.testbed_type != "suite-based":
            self.testbed_config = fun_test.get_asset_manager().get_test_bed_spec(self.testbed_type)
            fun_test.log("{} Testbed Config: {}".format(self.testbed_type, self.testbed_config))
            self.fs_hosts_map = parse_file_to_json(SCRIPTS_DIR + "/storage/pocs/apple/apple_fs_hosts_mapping.json")
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
        for dut_index in self.available_dut_indexes:
            self.topology_helper.set_dut_parameters(
                dut_index=dut_index,
                f1_parameters={0: {"boot_args": self.bootargs[0]},
                               1: {"boot_args": self.bootargs[1]}})
        self.topology = self.topology_helper.deploy()
        fun_test.test_assert(self.topology, "Topology deployed")

        # Datetime required for daily Dashboard data filter
        self.db_log_time = get_data_collection_time()
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

            # Stopping iptables service on all hosts
            host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
            host_handle.sudo_command("systemctl stop irqbalance")
            irq_bal_stat = host_handle.command("systemctl status irqbalance")
            if "dead" in irq_bal_stat:
                fun_test.log("IRQ balance stopped on host: {}".format(host_name))
            else:
                fun_test.log("IRQ balance not stopped on host: {}".format(host_name))
                host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

        # Ensuring connectivity from Host to F1's
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            for index, ip in enumerate(self.f1_ips):
                ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(host_name, self.funcp_spec[0]["container_names"][index], ip))

    def cleanup(self):
        pass


class WorkloadTriggerTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict[testcase].items():
            setattr(self, k, v)

        fun_test.log("Config Config: {}".format(self.__dict__))

        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

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
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        fun_test.shared_variables["transport_type"] = self.transport_type

        print("test level setup: self.host_info is: {}".format(self.host_info))

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["nvme_connect"] = False
            fun_test.shared_variables["blt"]["warmup_io_completed"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # Compute the individual BLT sizes
            self.capacity = int(
                ceil(self.stripe_details["vol_size"] / (self.blt_count * self.blt_details["block_size"]))
                * self.blt_details["block_size"]
            )

            # Create BLTs for striped volume
            self.stripe_unit_size = self.stripe_details["block_size"] * self.stripe_details["stripe_unit"]
            self.blt_capacity = self.stripe_unit_size + self.capacity
            if (self.blt_capacity / self.stripe_unit_size) % 2:
                fun_test.log("Num of block in BLT is not even")
                self.blt_capacity += self.stripe_unit_size

            self.thin_uuid = []
            for i in range(1, self.blt_count + 1, 1):
                cur_uuid = generate_uuid()
                self.thin_uuid.append(cur_uuid)
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_capacity,
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i, cur_uuid))
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid

            self.strip_vol_size = (self.blt_capacity - self.stripe_unit_size) * self.blt_count
            # Create Strip Volume
            self.stripe_uuid = generate_uuid()
            command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                                   capacity=self.strip_vol_size,
                                                                   name="stripevol1",
                                                                   uuid=self.stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))

            # Create TCP controllers for first host
            self.ctrlr_uuid = []
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    self.ctrlr_uuid.append(utils.generate_uuid())
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                               transport=self.transport_type.upper(),
                                                                               remote_ip=
                                                                               self.host_info[host_name]["ip"][0],
                                                                               nqn=self.nvme_subsystem,
                                                                               port=self.transport_port,
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Create Storage Controller for {} with controller uuid {} on DUT".
                                         format(self.transport_type.upper(), self.ctrlr_uuid[-1]))

                    # Attaching volume to NVMeOF controller
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[index],
                        ns_id=self.stripe_details["ns_id"],
                        vol_uuid=self.stripe_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Attach NVMeOF controller {} to stripe vol {} over {}".
                                         format(self.ctrlr_uuid[index], self.stripe_uuid,
                                                self.transport_type.upper()))

            # Starting packet capture in all the hosts
            self.pcap_started = {}
            self.pcap_stopped = {}
            self.pcap_pid = {}
            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    test_interface = self.host_info[host_name]["test_interface"].name
                    self.pcap_started[host_name] = False
                    self.pcap_stopped[host_name] = True
                    self.pcap_pid[host_name] = {}
                    self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                        interface=test_interface, tcpdump_filename="/tmp/nvme_connect.pcap", snaplen=1500)
                    if self.pcap_pid[host_name]:
                        fun_test.log("Started packet capture in {}".format(host_name))
                        self.pcap_started[host_name] = True
                        self.pcap_stopped[host_name] = False
                    else:
                        fun_test.critical("Unable to start packet capture in {}".format(host_name))

                    if not fun_test.shared_variables["blt"]["nvme_connect"]:
                        # Checking nvme-connect status
                        if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                nvme_io_queues=self.nvme_io_queues,
                                hostnqn=self.host_info[host_name]["ip"][0])
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                hostnqn=self.host_info[host_name]["ip"][0])

                        if self.pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                            self.pcap_stopped[host_name] = True

                        fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                        lsblk_output = host_handle.lsblk("-b")
                        fun_test.simple_assert(lsblk_output, "Listing available volumes")

                        volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                        host_handle.sudo_command("dmesg")
                        lsblk_output = host_handle.lsblk()
                        fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                                      message="{} device type check".format(volume_name))

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))
            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

            before_write_eqm = {}
            after_write_eqm = {}
            before_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]

                    # Create filesystem if needed else write to raw device
                    if hasattr(self, "create_file_system") and self.create_file_system:
                        host_handle.sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
                        host_handle.sudo_command("mount {} /mnt".format(self.nvme_block_device))
                        fun_test.log("Creating a testfile on XFS volume")
                        fio_output = host_handle.pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
                        host_handle.sudo_command("umount /mnt")
                        # Mount NVMe disk on host in Read-Only mode if on a filesystem
                        host_handle.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
                    else:
                        fio_output = host_handle.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Writing the entire volume")
                    fun_test.shared_variables["blt"]["warmup_io_completed"] = True
                    # host_handle.disconnect()

            after_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in before_write_eqm["data"].items():
                current_value = after_write_eqm["data"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    stats_delta = current_value - value
                    fun_test.log("Write test : there is a mismatch in {} : {}".format(field, stats_delta))

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):
        testcase = self.__class__.__name__

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}

        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = self.nvme_block_device
        volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])

        fio_size = int(100 / (self.num_hosts - 1))
        self.fio_cmd_args1["size"] = "{}{}".format(str(fio_size), "%")
        print("self.fio_cmd_args_fio_size is: {}".format(self.fio_cmd_args1["size"]))

        fio_offset_diff = fio_size

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}

            test_thread_id = {}
            host_clone = {}

            for index, host_name in enumerate(self.host_info):
                '''
                host_numa_cpus = self.host_info[host_name]["host_numa_cpus"]
                total_numa_cpus = self.host_info[host_name]["total_numa_cpus"]
                '''

                print("print: run: current index is: {}".format(index))
                if index != 0:
                    # Create NVMe-OF controller for rest of hosts
                    self.ctrlr_uuid.append(utils.generate_uuid())
                    command_result = self.storage_controller.create_controller(
                        ctrlr_uuid=self.ctrlr_uuid[-1], transport=self.transport_type.upper(),
                        remote_ip=self.host_info[host_name]["ip"][0], nqn=self.nvme_subsystem, port=self.transport_port,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Create Storage Controller for {} with controller uuid {} on DUT".
                                         format(self.transport_type.upper(), self.ctrlr_uuid[-1]))

                    # Attach volume to NVMe-OF controller
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[-1], ns_id=self.stripe_details["ns_id"],
                        vol_uuid=self.stripe_uuid, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Attach NVMeOF controller {} to stripe vol {} over {}".format(
                                             self.ctrlr_uuid[-1], self.stripe_uuid, self.transport_type.upper()))

                    # NVMe connect
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    test_interface = self.host_info[host_name]["test_interface"].name
                    self.pcap_started[host_name] = False
                    self.pcap_stopped[host_name] = True
                    self.pcap_pid[host_name] = {}
                    self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                        interface=test_interface, tcpdump_filename="/tmp/nvme_connect.pcap", snaplen=1500)
                    if self.pcap_pid[host_name]:
                        fun_test.log("Started packet capture in {}".format(host_name))
                        self.pcap_started[host_name] = True
                        self.pcap_stopped[host_name] = False
                    else:
                        fun_test.critical("Unable to start packet capture in {}".format(host_name))

                    if not fun_test.shared_variables["blt"]["nvme_connect"]:
                        # Checking nvme-connect status
                        if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                nvme_io_queues=self.nvme_io_queues,
                                hostnqn=self.host_info[host_name]["ip"][0])
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                hostnqn=self.host_info[host_name]["ip"][0])

                        if self.pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                            self.pcap_stopped[host_name] = True

                        fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                        lsblk_output = host_handle.lsblk("-b")
                        fun_test.simple_assert(lsblk_output, "Listing available volumes")

                        host_handle.sudo_command("dmesg")
                        lsblk_output = host_handle.lsblk()
                        fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                                      message="{} device type check".format(volume_name))

                wait_time = self.num_hosts - index
                print("print: run: wait time is: {}".format(wait_time))
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                if index == 0:
                    # Starting Read for whole volume on first host
                    fun_test.log("print: run: if index == 0: starting IO on host: {}".format(host_name))
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args)
                else:
                    # Starting IO on rest of hosts for particular LBA range
                    fun_test.log("print: run: else index == 0: starting IO on host: {}".format(host_name))
                    self.fio_cmd_args1["offset"] = "{}{}".format(str((index - 1) * fio_offset_diff), "%")
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args1)

            # Waiting for all the FIO test threads to complete
            try:
                fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                for index, host_name in enumerate(self.host_info):
                    fio_output[iodepth][host_name] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                           fun_test.shared_variables["fio"][index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
            finally:
                self.storage_controller.verbose = True

            # Summing up the FIO stats from all the hosts
            for index, host_name in enumerate(self.host_info):
                fun_test.test_assert(fun_test.shared_variables["fio"][index], "FIO test with on {}".format(host_name))
                for op, stats in fun_test.shared_variables["fio"][index].items():
                    if op not in aggr_fio_output[iodepth]:
                        aggr_fio_output[iodepth][op] = {}
                    aggr_fio_output[iodepth][op] = Counter(aggr_fio_output[iodepth][op]) + \
                                                   Counter(fun_test.shared_variables["fio"][index][op])

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            for op, stats in aggr_fio_output[iodepth].items():
                for field, value in stats.items():
                    if field == "iops":
                        aggr_fio_output[iodepth][op][field] = int(round(value))
                    if field == "bw":
                        # Converting the KBps to MBps
                        aggr_fio_output[iodepth][op][field] = int(round(value / 1000))
                    if "latency" in field:
                        aggr_fio_output[iodepth][op][field] = int(round(value) / self.num_hosts)

            fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            if not aggr_fio_output[iodepth]:
                fio_result[iodepth] = False
                fun_test.critical("No output from FIO test, hence moving to the next variation")
                continue

            fun_test.sleep("Waiting in between iterations", self.iter_interval)

        iodepth = self.fio_iodepth[0]
        fun_test.log("\n********** Starting Disconnect test **********\n")
        for index, host_name in enumerate(self.host_info):
            print("print: disconnect run: current index is: {}".format(index))

            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()

            if index == 0:
                # Starting Read for whole volume on first host
                fun_test.log("print: diconnect run: if index == 0: starting IO on host: {}".format(host_name))
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      iodepth=iodepth,
                                                                      name="detach_fio_{}".format(host_name),
                                                                      **self.fio_cmd_args)
            else:
                # Starting IO on rest of hosts for particular LBA range
                fun_test.log("print: disconnect run: else index == 0: starting IO on host: {}".format(host_name))
                self.fio_cmd_args1["offset"] = "{}{}".format(str((index - 1) * fio_offset_diff), "%")
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      iodepth=iodepth,
                                                                      name="detach_fio_{}".format(host_name),
                                                                      **self.fio_cmd_args1)

            fun_test.sleep("to initiate detach from host", self.detach_time)
            # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
            nvme_disconnect_cmd = "nvme disconnect -d {}".format(volume_name)

            if index != 0:
                # Executing NVMe disconnect from all the hosts
                host_handle = self.host_info[host_name]["handle"]
                host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="{} - NVME Disconnect Status".format(host_name))

                # Detach volume from NVMe-OF controller
                command_result = self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=self.ctrlr_uuid[index], ns_id=self.stripe_details["ns_id"],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "{} - Detach NVMeOF controller {}".format(
                    host_name, self.ctrlr_uuid[index]))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[iodepth][host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        finally:
            self.storage_controller.verbose = True

        # Summing up the FIO stats from all the hosts
        for index, host_name in enumerate(self.host_info):
            if index == 0:
                fun_test.test_assert(fun_test.shared_variables["fio"][index], "FIO test with on {}".format(host_name))
            else:
                # TODO: Capture the failure
                fun_test.log("FIO test with on {}: {}".format(host_name, fun_test.shared_variables["fio"][index]))
                fun_test.test_assert_expected(expected={}, actual=fun_test.shared_variables["fio"][index],
                                              message="Expected IO failure due to Detach")

        fun_test.log("\n********** Starting Re-Attach hosts test **********\n")
        for index, host_name in enumerate(self.host_info):
            print("print: Reattach run: current index is: {}".format(index))

            if index != 0:
                # Re-Attach volume to NVMe-OF controller
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[index], ns_id=self.stripe_details["ns_id"],
                    vol_uuid=self.stripe_uuid, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Re-Attach NVMeOF controller {} to stripe vol {} over {}".format(
                                         self.ctrlr_uuid[index], self.stripe_uuid, self.transport_type.upper()))

                # NVMe connect
                fun_test.shared_variables["blt"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]
                test_interface = self.host_info[host_name]["test_interface"].name
                self.pcap_started[host_name] = False
                self.pcap_stopped[host_name] = True
                self.pcap_pid[host_name] = {}
                self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                    interface=test_interface, tcpdump_filename="/tmp/nvme_reconnect.pcap", snaplen=1500)
                if self.pcap_pid[host_name]:
                    fun_test.log("Started packet capture in {}".format(host_name))
                    self.pcap_started[host_name] = True
                    self.pcap_stopped[host_name] = False
                else:
                    fun_test.critical("Unable to start packet capture in {}".format(host_name))

                if not fun_test.shared_variables["blt"]["nvme_connect"]:
                    # Checking nvme-connect status
                    if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.transport_type.lower(),
                            nvme_io_queues=self.nvme_io_queues,
                            hostnqn=self.host_info[host_name]["ip"][0])
                    else:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.transport_type.lower(),
                            hostnqn=self.host_info[host_name]["ip"][0])

                    if self.pcap_started[host_name]:
                        host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                        self.pcap_stopped[host_name] = True

                    fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                    lsblk_output = host_handle.lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")

                    # volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                    host_handle.sudo_command("dmesg")
                    lsblk_output = host_handle.lsblk()
                    fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                    fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                                  message="{} device type check".format(volume_name))

            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()

            if index == 0:
                # Starting Read for whole volume on first host
                fun_test.log("print: Reattach run: if index == 0: starting IO on host: {}".format(host_name))
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      iodepth=iodepth,
                                                                      name="detach_fio_{}".format(host_name),
                                                                      **self.fio_cmd_args)
            else:
                # Starting IO on rest of hosts for particular LBA range
                fun_test.log("print: reattach run: else index == 0: starting IO on host: {}".format(host_name))
                self.fio_cmd_args1["offset"] = "{}{}".format(str((index - 1) * fio_offset_diff), "%")
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      iodepth=iodepth,
                                                                      name="detach_fio_{}".format(host_name),
                                                                      **self.fio_cmd_args1)
        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[iodepth][host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        finally:
            self.storage_controller.verbose = True

    def cleanup(self):
        try:
            # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                             source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                             source_file_path="/tmp/nvme_connect.pcap", target_file_path=pcap_artifact_file)
                fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                            filename=pcap_artifact_file)
                if index != 0:
                    pcap_post_fix_name = "{}_nvme_reconnect.pcap".format(host_name)
                    pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path="/tmp/nvme_reconnect.pcap", target_file_path=pcap_artifact_file)
                    fun_test.add_auxillary_file(description="Host {} NVME re-connect pcap".format(host_name),
                                                filename=pcap_artifact_file)
        except Exception as ex:
            fun_test.critical(str(ex))


class StripedVolVerifyIO(WorkloadTriggerTestCase):
    def describe(self):
        self.set_test_details(
            id=1,
            summary="Create Stripe Volume and validate events",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host and perform sequential write
                3. Start Random Read on whole volume from first host
                4. Start Random Read-Write with data integrity from rest of the volumes
                5. Ensure data integrity
                6. Initiate IO again and Disconnect hosts one by one
                7. Verify impact on IO
                8. Re-attach hosts and initiate IO again 
                ''')

    def setup(self):
        super(StripedVolVerifyIO, self).setup()

    def run(self):
        super(StripedVolVerifyIO, self).run()

    def cleanup(self):
        super(StripedVolVerifyIO, self).cleanup()


if __name__ == "__main__":
    testscript = WorkloadTriggerTestScript()
    testscript.add_test_case(StripedVolVerifyIO())
    testscript.run()
