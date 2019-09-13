from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from lib.system.utils import *
from lib.host.storage_controller import *
from collections import OrderedDict
from math import ceil


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def allow_host_access(sc_obj, host_ip, host_index, vol_uuid):
    cur_uuid = generate_uuid()
    nqn = "nqn" + str(host_index + 1)
    nvme_transport = "tcp"
    transport_port = 1099

    # Create NVMe-OF controller
    command_result = sc_obj.create_controller(ctrlr_uuid=cur_uuid,
                                              transport=nvme_transport.upper(),
                                              remote_ip=host_ip,
                                              nqn=nqn,
                                              port=transport_port,
                                              command_duration=5)

    fun_test.log(command_result)
    fun_test.test_assert(command_result["status"], "Create storage controller for TCP with uuid {} on DUT".
                         format(cur_uuid))

    # Attach volume to NVMe-OF controller
    ns_id = host_index + 1
    command_result = sc_obj.attach_volume_to_controller(ctrlr_uuid=cur_uuid,
                                                        ns_id=ns_id,
                                                        vol_uuid=vol_uuid)

    fun_test.log(command_result)
    fun_test.test_assert(command_result["status"], "Attach NVMeOF controller {} to stripe vol {} over {}".
                         format(cur_uuid, vol_uuid, nvme_transport))


def nvme_connect(host, host_index, f1_ip):
        nqn = "nqn" + str(host_index + 1)
        ns_id = host_index + 1
        nvme_io_queues = 16
        nvme_transport = "tcp"
        transport_port = 1099
        nvme_device = "/dev/nvme0"

        host_instance = host["host_instance"]
        host_instance.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
        host_instance.sudo_command("systemctl stop irqbalance")
        irq_bal_stat = host_instance.command("systemctl status irqbalance")
        if "dead" in irq_bal_stat:
            fun_test.log("IRQ balance stopped on {}".format(host_index))
        else:
            fun_test.log("IRQ balance not stopped on {}".format(host_index))
            host_instance.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

        # Interface name is not always fixed; filtering on IP of F1 instead (assuming 1 IP for now)
        host_instance.start_bg_process(command="sudo tcpdump -i any host {} -w nvme_connect_auto.pcap"
                                       .format(f1_ip))
        command_result = host_instance.sudo_command(
                "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(nvme_transport.lower(),
                                                                          f1_ip,
                                                                          transport_port,
                                                                          nqn,
                                                                          nvme_io_queues,
                                                                          host["host_ip"]))
        fun_test.log("nvme_connect command result is: {}".format(command_result))
        print("last command status is: {}".format(host_instance.exit_status))

        fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
        host_instance.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
        volume_name = nvme_device.replace("/dev/", "") + "n" + str(ns_id)
        print("exprected vol name: {}".format(volume_name))
        host_instance.sudo_command("dmesg")
        lsblk_output = host_instance.lsblk()
        fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                      message="{} device type check".format(volume_name))


class WorkloadTriggerTestScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        """)

    def setup(self):

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = parse_file_to_json(config_file)

        fun_test.shared_variables["fio"] = {}
        fun_test.shared_variables["iostat_output"] = {}

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 2
            self.command_timeout = 30
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

        # Deploying of DUTs
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
        # fun_test.shared_variables["num_hosts"] = self.num_hosts

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
        print("script setup: prepared host_info is: {}".format(self.host_info))
        print("script setup: dir of host_info is: {}".format(dir(self.host_info)))

        # Rebooting all the hosts in non-blocking mode before the test and getting NUMA cpus
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            '''
            # Enable only if NUMA node required
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
            '''
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
                mode=self.funcp_mode, launch_resp_parse=True)
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


class CreateStripedVolTestCase(FunTestCase):
    def describe(self):
        self.set_test_details(
            id=1,
            summary="",
            steps='''
                Blank
                ''')

    def setup(self):
        testcase = self.__class__.__name__

        benchmark_parsing = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = parse_file_to_json(benchmark_file)

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        '''
        if not hasattr(self, "num_ssd"):
            self.num_ssd = 6
        if not hasattr(self, "blt_count"):
            self.blt_count = 6
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count
        '''

        # New changes
        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

        '''
        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.host_list = fun_test.shared_variables["host_list"]
        '''

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

        # self.num_hosts = fun_test.shared_variables["num_hosts"]
        '''
        self.final_host_ips = self.host_ips[:]
        print("self.final_host_ips: {}".format(self.final_host_ips))
        if len(self.host_ips) < self.num_hosts:
            print("len of self.host_ips is less than self.num_hosts")
            for i in range(len(self.host_ips), self.num_hosts):
                self.final_host_ips.append(self.host_ips[len(self.host_ips) % i])
        fun_test.shared_variables["final_host_ips"] = self.final_host_ips
        '''

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
            self.stripe_uuid = []
            stripe_uuid = generate_uuid()
            self.stripe_uuid.append(stripe_uuid)
            command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                                   capacity=self.strip_vol_size,
                                                                   name="stripevol1",
                                                                   uuid=stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))
            fun_test.shared_variables["stripe_uuid"] = self.stripe_uuid

            # Create TCP controllers for all hosts
            self.ctrlr_uuid = []
            for host_name in self.host_info:
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_info[host_name]["ip"][0],
                                                                           nqn=self.nvme_subsystem,
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Create Storage Controller for {} with controller uuid {} on DUT".
                                     format(self.transport_type.upper(), self.ctrlr_uuid[-1]))

            # Attaching volume to NVMeOF controller
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[index],
                        ns_id=self.ns_id,
                        vol_uuid=self.stripe_uuid[0])
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Attach NVMeOF controller {} to stripe vol {} over {}".
                                         format(self.ctrlr_uuid[index], self.stripe_uuid[0],
                                                self.transport_type.upper()))

            '''
            # Create TCP controller for 1st host
            self.ctrlr_uuid = []
            fun_test.shared_variables["host_count"] = self.num_hosts
            nvme_transport = self.transport_type

            host_index = 0
            cur_uuid = generate_uuid()
            self.ctrlr_uuid.append(cur_uuid)
            self.nqn = "nqn" + str(host_index + 1)

            # Create NVMe-OF controller
            command_result = self.storage_controller.create_controller(ctrlr_uuid=cur_uuid,
                                                                       transport=nvme_transport.upper(),
                                                                       remote_ip=self.host_list[host_index]["host_ip"],
                                                                       nqn=self.nqn,
                                                                       port=self.transport_port,
                                                                       command_duration=5)

            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create storage controller for TCP with uuid {} on DUT".
                                 format(cur_uuid))

            # Attach volume to NVMe-OF controller
            self.ns_id = host_index + 1
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=cur_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=self.stripe_uuid)

            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attach NVMeOF controller {} to stripe vol {} over {}".
                                 format(cur_uuid, self.stripe_uuid, nvme_transport))

            self.nqn = "nqn" + str(host_index + 1)

            self.host_instance = self.host_list[host_index]["host_instance"]
            self.host_instance.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
            self.host_instance.sudo_command("systemctl stop irqbalance")
            irq_bal_stat = self.host_instance.command("systemctl status irqbalance")
            if "dead" in irq_bal_stat:
                fun_test.log("IRQ balance stopped on {}".format(host_index))
            else:
                fun_test.log("IRQ balance not stopped on {}".format(host_index))
                self.host_instance.sudo_command("tuned-adm profile network-throughput && tuned-adm active")
            '''

            # Starting packet capture in all the hosts
            pcap_started = {}
            pcap_stopped = {}
            pcap_pid = {}
            self.host_info_list = list(self.host_info.items())
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    host_name = self.host_info_list[index][0]
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    test_interface = self.host_info[host_name]["test_interface"].name
                    pcap_started[host_name] = False
                    pcap_stopped[host_name] = True
                    pcap_pid[host_name] = {}
                    pcap_pid[host_name] = host_handle.tcpdump_capture_start(interface=test_interface,
                                                                            tcpdump_filename="/tmp/nvme_connect.pcap",
                                                                            snaplen=1500)
                    if pcap_pid[host_name]:
                        fun_test.log("Started packet capture in {}".format(host_name))
                        pcap_started[host_name] = True
                        pcap_stopped[host_name] = False
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

                        if pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                            pcap_stopped[host_name] = True

                        fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                        lsblk_output = host_handle.lsblk("-b")
                        fun_test.simple_assert(lsblk_output, "Listing available volumes")

                        volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                        host_handle.sudo_command("dmesg")
                        lsblk_output = host_handle.lsblk()
                        fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                                      message="{} device type check".format(volume_name))

            '''
            # Interface name is not always fixed; filtering on IP of F1 instead (assuming 1 IP for now)
            self.host_instance.start_bg_process(command="sudo tcpdump -i any host {} -w nvme_connect_auto.pcap"
                                                .format(self.test_network["f1_loopback_ip"]))
            if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                command_result = self.host_instance.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(self.transport_type.lower(),
                                                                              self.test_network["f1_loopback_ip"],
                                                                              self.transport_port,
                                                                              self.nqn,
                                                                              self.nvme_io_queues,
                                                                              self.host_list[host_index]["host_ip"]))
                fun_test.log(command_result)
            else:
                command_result = self.host_instance.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".format(self.transport_type.lower(),
                                                                        self.test_network["f1_loopback_ip"],
                                                                        str(self.transport_port),
                                                                        self.nqn,
                                                                        self.host_list[host_index]["host_ip"]))
                fun_test.log(command_result)
            fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
            self.host_instance.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
            '''

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
                    host_handle.disconnect()

            after_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in before_write_eqm["data"].items():
                current_value = after_write_eqm["data"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    stats_delta = current_value - value
                    fun_test.log("Write test : there is a mismatch in {} : {}".format(field, stats_delta))

            '''
            # Mount NVMe disk on host in Read-Only mode if on a filesystem
            if hasattr(self, "create_file_system") and self.create_file_system:
                self.host_instance.sudo_command("umount /mnt")
                self.host_instance.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
            self.host_instance.disconnect()
            '''

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):
        testcase = self.__class__.__name__

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}
            fio_job_args = ""
            fio_cmd_args = {}

            test_thread_id = {}
            host_clone = {}

            for index, host_name in enumerate(self.host_info):
                fio_job_args = ""
                host_handle = self.host_info[host_name]["handle"]
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                host_numa_cpus = self.host_info[host_name]["host_numa_cpus"]
                total_numa_cpus = self.host_info[host_name]["total_numa_cpus"]
                fio_num_jobs = len(nvme_block_device_list)

                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      numjobs=fio_num_jobs,
                                                                      iodepth=fio_iodepth, name=fio_job_name,
                                                                      cpus_allowed=host_numa_cpus,
                                                                      **self.fio_cmd_args)

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
                fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                     "FIO {} test with the Block Size {} IO depth {} and Numjobs {} on {}"
                                     .format(row_data_dict["mode"], fio_block_size, fio_iodepth,
                                             fio_num_jobs * global_num_jobs, host_name))
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
                    row_data_dict[op + field] = aggr_fio_output[iodepth][op][field]

            fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            if not aggr_fio_output[iodepth]:
                fio_result[iodepth] = False
                fun_test.critical("No output from FIO test, hence moving to the next variation")
                continue

            fun_test.sleep("Waiting in between iterations", self.iter_interval)


        thread_id = {}
        end_host_thread = {}
        thread_count = 1
        wait_time = self.num_hosts + 1 - thread_count
        end_host_thread[thread_count] = self.host_list[host_index]["host_instance"].clone()

        # Start read traffic from the host
        # TODO: Change to non-blocking mode
        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = self.nvme_block_device

        thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                func=fio_parser,
                                                                arg1=end_host_thread[thread_count],
                                                                host_index=thread_count,
                                                                filename=test_filename,
                                                                rw="randread",
                                                                **self.fio_cmd_args)
        fun_test.test_assert(fio_output, "Reading from filesystem")
        self.host_instance.disconnect()

        print("tc1: run: host_index is: {}".format(host_index))
        fun_test.shared_variables["host_index"] = host_index

    def cleanup(self):
        pass


class ConnectMoreHosts(FunTestCase):
    def describe(self):
        self.set_test_details(
            id=2,
            summary="",
            steps='''
                Blank
                ''')

    def setup(self):
        pass

    def run(self):
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = parse_file_to_json(benchmark_file)

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        self.fs = fun_test.shared_variables["fs_obj"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.host_list = fun_test.shared_variables["host_list"]
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = fun_test.shared_variables["num_hosts"]

        self.stripe_uuid = fun_test.shared_variables["stripe_uuid"]

        # Create controller for 2nd host
        host_index = fun_test.shared_variables["host_index"] + 1
        print("tc2: run: host_index is: {}".format(host_index))

        allow_host_access(self.storage_controller, self.host_list[host_index]["host_ip"], host_index, self.stripe_uuid)

        nvme_connect(self.host_list[host_index], host_index, self.test_network["f1_loopback_ip"])

        self.host_instance = self.host_list[host_index]["host_instance"]

        # Mount NVMe disk on host in Read-Only mode if on a filesystem
        if hasattr(self, "create_file_system") and self.create_file_system:
            self.host_instance.sudo_command("umount /mnt")
            self.host_instance.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
        self.host_instance.disconnect()

        # Start read traffic from the host
        # TODO: Change to non-blocking mode
        if hasattr(self, "create_file_system") and self.create_file_system:
            fio_output = self.host_instance.pcie_fio(filename="/mnt/testfile.dat",
                                                     **self.fio_cmd_args)
        else:
            fio_output = self.host_instance.pcie_fio(filename=self.nvme_block_device, **self.fio_cmd_args)
        fun_test.test_assert(fio_output, "Reading from filesystem")
        self.host_instance.disconnect()

    def cleanup(self):
        pass


if __name__ == "__main__":
    testscript = WorkloadTriggerTestScript()
    testscript.add_test_case(CreateStripedVolTestCase())
    testscript.add_test_case(ConnectMoreHosts())
    testscript.run()
