from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from lib.templates.storage.storage_controller_api import *
from scripts.storage.storage_helper import *
from lib.system.utils import *
from lib.host.storage_controller import *
from collections import OrderedDict, Counter
from math import ceil


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.log("Fio test for thread {}: {}".format(host_index, fio_output))
    arg1.disconnect()


class StripeVolAttachDetachTestScript(FunTestScript):
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
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]

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
            # Removing existing db directories for fresh setup
            try:
                if self.cleanup_sc_db:
                    for directory in self.sc_db_directories:
                        if self.come_obj[index].check_file_directory_exists(path=directory):
                            fun_test.log("Removing Directory {}".format(directory))
                            self.come_obj[index].sudo_command("rm -rf {}".format(directory))
                            fun_test.test_assert_expected(actual=self.come_obj[index].exit_status(), expected=0,
                                                          message="Directory {} is removed".format(directory))
                        else:
                            fun_test.log("Directory {} does not exist skipping deletion".format(directory))
            except Exception as ex:
                fun_test.critical(str(ex))

            self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
            self.funcp_spec[index] = self.funcp_obj[index].deploy_funcp_container(
                update_deploy_script=self.update_deploy_script, update_workspace=self.update_workspace,
                mode=self.funcp_mode, include_storage=True)

            fun_test.test_assert(self.funcp_spec[index]["status"],
                                 "Starting FunCP docker container in DUT {}".format(index))
            self.funcp_spec[index]["container_names"].sort()

            # Ensure that that FPGO interface is up both the docker containers
            for f1_index, container_name in enumerate(self.funcp_spec[index]["container_names"]):
                status = self.funcp_obj[index].container_info[container_name].ifconfig_up_down("fpg0", "up")
                fun_test.test_assert(status, "FPG0 interface up in {}".format(container_name))
        # Creating storage controller API object for the first DUT in the current setup
        fun_test.sleep("", 60)
        self.sc_api_obj = StorageControllerApi(api_server_ip=self.come_obj[0].host_ip,
                                               api_server_port=self.api_server_port, username=self.api_server_username,
                                               password=self.api_server_password)
        # Getting all the DUTs of the setup
        nodes = self.sc_api_obj.get_dpu_ids()
        fun_test.test_assert(nodes, "Getting UUIDs of all DUTs in the setup")
        for index, node in enumerate(nodes):
            # Extracting the DUT's bond interface details and applying it to FPG0 for now, due to SC bug
            ip = self.fs_spec[index / 2].spec["bond_interface_info"][str(index % 2)][str(0)]["ip"]
            ip = ip.split('/')[0]
            subnet_mask = self.fs_spec[index / 2].spec["bond_interface_info"][str(index % 2)][str(0)]["subnet_mask"]
            route = self.fs_spec[index / 2].spec["bond_interface_info"][str(index % 2)][str(0)]["route"][0]
            next_hop = "{}/{}".format(route["gateway"], route["network"].split("/")[1])
            self.f1_ips.append(ip)

            fun_test.log("Current {} node's FPG0 is going to be configured with {} IP address with {} subnet mask with"
                         " next hop set to {}".format(node, ip, subnet_mask, next_hop))
            result = self.sc_api_obj.configure_dataplane_ip(dpu_id=node, interface_name="fpg0", ip=ip,
                                                            subnet_mask=subnet_mask, next_hop=next_hop, use_dhcp=False)
            fun_test.log("Dataplane IP configuration result of {}: {}".format(node, result))
            fun_test.test_assert(result["status"], "Configuring {} DUT with Dataplane IP {}".format(node, ip))

        # Forming shared variables for defined parameters
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_obj
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_obj
        fun_test.shared_variables["sc_obj"] = self.sc_obj
        fun_test.shared_variables["sc_api_obj"] = self.sc_api_obj
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

        if fun_test.shared_variables["stripe_vol"]["setup_created"]:
            self.stripe_uuid = fun_test.shared_variables["stripe_uuid"]
            self.detach_uuid = fun_test.shared_variables["detach_uuid"]
            self.volume_name = fun_test.shared_variables["volume_name"]
            self.nqn = fun_test.shared_variables["nqn"]
            self.attach_detach_count = fun_test.shared_variables["attach_detach_count"]
            self.testcase = fun_test.shared_variables["testcase"]

            if fun_test.shared_variables["attach_detach_loop"]:
                for iteration in range(self.attach_detach_count):
                    for index, host_name in enumerate(self.host_info):
                        host_handle = self.host_info[host_name]["handle"]
                        try:
                            # Saving the pcap file captured during the nvme connect to the pcap_artifact_file
                            pcap_post_fix_name = "{}_nvme_connect_iter_{}.pcap".format(host_name, iteration)
                            pcap_artifact_file = fun_test.get_test_case_artifact_file_name(
                                post_fix_name=pcap_post_fix_name)
                            fun_test.scp(source_port=host_handle.ssh_port,
                                         source_username=host_handle.ssh_username,
                                         source_password=host_handle.ssh_password,
                                         source_ip=host_handle.host_ip,
                                         source_file_path="/tmp/nvme_connect_iter_{}.pcap".format(iteration),
                                         target_file_path=pcap_artifact_file)
                            fun_test.add_auxillary_file(description="{}: Host {} NVME connect pcap iteration {}".
                                                        format(self.testcase, host_name, iteration),
                                                        filename=pcap_artifact_file)
                        except Exception as ex:
                            fun_test.critical(str(ex))

            # Volume un-configuration
            if not fun_test.shared_variables["attach_detach_loop"]:
                try:
                    for index, host_name in enumerate(self.host_info):
                        # NVMe disconnect on host
                        # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)  # TODO: SWOS-6165
                        nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)
                        host_handle = self.host_info[host_name]["handle"]
                        host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                        nvme_disconnect_exit_status = host_handle.exit_status()
                        fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                      message="{} - NVME Disconnect Status".format(host_name))
                        # Detaching volume
                        detach_volume = self.sc_api_obj.detach_volume(port_uuid=self.detach_uuid)
                        fun_test.test_assert(detach_volume, "{} - Detach NVMeOF controller".format(host_name))
                except Exception as ex:
                    fun_test.critical(str(ex))

            try:
                # Delete Strip Volume
                fun_test.log("\n********** Deleting volume **********\n")
                delete_volume = self.sc_api_obj.delete_volume(vol_uuid=self.stripe_uuid)
                fun_test.test_assert(delete_volume, "Deleting Stripe Vol with uuid {} on DUT".format(self.stripe_uuid))
            except Exception as ex:
                fun_test.critical(str(ex))


class StripeVolAttachDetachTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        self.testcase = self.__class__.__name__

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict[self.testcase].items():
            setattr(self, k, v)

        fun_test.log("Config Config: {}".format(self.__dict__))

        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.fs_obj = fun_test.shared_variables["fs_obj"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
        self.sc_api = fun_test.shared_variables["sc_api_obj"]
        self.f1_ips = fun_test.shared_variables["f1_ips"][self.f1_in_use]
        self.host_info = fun_test.shared_variables["host_info"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = len(self.host_info)
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        fun_test.shared_variables["transport_type"] = self.transport_type
        fun_test.shared_variables["testcase"] = self.testcase

        if "stripe_vol" not in fun_test.shared_variables or not fun_test.shared_variables["stripe_vol"]["setup_created"]:
            fun_test.shared_variables["stripe_vol"] = {}
            fun_test.shared_variables["stripe_vol"]["setup_created"] = False
            fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
            fun_test.shared_variables["stripe_vol"]["warmup_io_completed"] = False

            # Creating pool
            if self.create_pool:
                pass

            # Fetching pool uuid as per pool name provided
            pool_name = self.default_pool if not self.create_pool else self.pool_name
            self.pool_uuid = self.sc_api.get_pool_uuid_by_name(name=pool_name)

            # Creating strip volume using sc api
            create_stripe_vol = self.sc_api.create_stripe_volume(pool_uuid=self.pool_uuid, name="stripevol1",
                                                                 capacity=self.stripe_details["vol_size"],
                                                                 pvol_type=self.stripe_details["pvol_type"],
                                                                 stripe_count=self.stripe_details["stripe_count"],
                                                                 encrypt=self.stripe_details["encrypt"],
                                                                 allow_expansion=self.stripe_details["allow_expansion"],
                                                                 data_protection=self.stripe_details["data_protection"],
                                                                 compression_effort=self.stripe_details["compress"])
            fun_test.log("Create stripe volume API response: {}".format(create_stripe_vol))
            fun_test.test_assert(create_stripe_vol["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(create_stripe_vol["data"]["uuid"]))
            self.stripe_uuid = create_stripe_vol["data"]["uuid"]

            # Attaching volume to host
            # Starting packet capture in all the hosts
            self.pcap_started = {}
            self.pcap_stopped = {}
            self.pcap_pid = {}
            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                attach_volume = self.sc_api.volume_attach_remote(vol_uuid=self.stripe_uuid,
                                                                 transport=self.transport_type.upper(),
                                                                 remote_ip=self.host_info[host_name]["ip"][0])
                fun_test.log("Attach volume API response: {}".format(attach_volume))
                fun_test.test_assert(attach_volume["status"], "Attach Stripe volume {} over {} for host {}".
                                     format(self.stripe_uuid, self.transport_type.upper(), host_name))

                self.nqn = attach_volume["data"]["nqn"]
                self.detach_uuid = attach_volume["data"]["uuid"]
                fun_test.shared_variables["stripe_vol"][host_name] = {}
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

                if not fun_test.shared_variables["stripe_vol"]["nvme_connect"]:
                    # Checking nvme-connect status
                    if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=attach_volume["data"]["ip"], nvme_subsystem=self.nqn,
                            port=self.transport_port, transport=self.transport_type.lower(),
                            nvme_io_queues=self.nvme_io_queues, hostnqn=self.host_info[host_name]["ip"][0])
                    else:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=attach_volume["data"]["ip"], nvme_subsystem=self.nqn,
                            port=self.transport_port, transport=self.transport_type.lower(),
                            hostnqn=self.host_info[host_name]["ip"][0])

                    if self.pcap_started[host_name]:
                        host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                        self.pcap_stopped[host_name] = True

                    fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                    lsblk_output = host_handle.lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")

                    '''
                    self.host_info[host_name]["nvme_block_device_list"] = []
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                                     str(match.group(2))
                            if volume_name not in self.host_info[host_name]["nvme_block_device_list"]:
                                self.host_info[host_name]["nvme_block_device_list"].append(
                                    self.nvme_block_device)
                            fun_test.log("NVMe Block Device/s: {}".
                                         format(self.host_info[host_name]["nvme_block_device_list"]))

                    try:
                        fun_test.test_assert_expected(expected=len(self.host_info),
                                                      actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                                      message="Expected NVMe devices are available")
                    except Exception as ex:
                        fun_test.critical(str(ex))
                    fun_test.log("nvme_block_device_list: {}".
                                 format(self.host_info[host_name]["nvme_block_device_list"]))
                    self.volume_name = self.host_info[host_name]["nvme_block_device_list"][0]
                    '''
                    self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                    host_handle.sudo_command("dmesg")
                    lsblk_output = host_handle.lsblk()
                    fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".
                                         format(self.volume_name))
                    fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                                  message="{} device type check".format(self.volume_name))
                    fun_test.shared_variables["stripe_vol"]["nvme_connect"] = True

            # Leaving syslog level to default
            '''
            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))
            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")
            '''

            for index, host_name in enumerate(self.host_info):
                fun_test.shared_variables["stripe_vol"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]

                if self.io_during_attach_detach:
                    before_write_eqm = {}
                    after_write_eqm = {}
                    before_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")
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
                    fun_test.shared_variables["stripe_vol"]["warmup_io_completed"] = True

                    after_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")
                    for field, value in before_write_eqm["data"].items():
                        current_value = after_write_eqm["data"][field]
                        if (value != current_value) and (field != "incoming BN msg valid"):
                            stats_delta = current_value - value
                            fun_test.log("Write test : there is a mismatch in {} : {}".format(field, stats_delta))

                if self.attach_detach_loop:
                    # Disconnecting volume from host
                    try:
                        fun_test.log("Disconnecting volume from the host")
                        # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)  # TODO: SWOS-6165
                        nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)
                        host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                        nvme_disconnect_exit_status = host_handle.exit_status()
                        fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                      message="{} - NVME Disconnect Status".format(host_name))
                        fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    # Detaching volume
                    detach_volume = self.sc_api.detach_volume(port_uuid=self.detach_uuid)
                    fun_test.log("Detach volume API response: {}".format(detach_volume))
                    fun_test.test_assert(detach_volume, "{} - Detach Volume".format(host_name))

            fun_test.shared_variables["stripe_vol"]["setup_created"] = True
            fun_test.shared_variables["stripe_uuid"] = self.stripe_uuid
            fun_test.shared_variables["detach_uuid"] = self.detach_uuid
            fun_test.shared_variables["attach_detach_loop"] = self.attach_detach_loop
            fun_test.shared_variables["storage_controller"] = self.storage_controller
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["nqn"] = self.nqn

    def run(self):
        testcase = self.__class__.__name__

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_output = {}
        test_thread_id = {}
        host_clone = {}
        self.pcap_started = {}
        self.pcap_stopped = {}
        self.pcap_pid = {}

        self.stripe_uuid = fun_test.shared_variables["stripe_uuid"]
        fun_test.shared_variables["attach_detach_count"] = self.attach_detach_count

        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = self.nvme_block_device

        if self.attach_detach_loop:
            for iteration in range(self.attach_detach_count):
                fun_test.log("Iteration: {} - Executing Attach Detach in loop".format(iteration))
                fun_test.sleep("before attaching volume", self.attach_detach_wait)
                self.pcap_started[iteration] = {}
                self.pcap_stopped[iteration] = {}
                self.pcap_pid[iteration] = {}

                for index, host_name in enumerate(self.host_info):
                    # Attaching volume to NVMeOF controller
                    host_handle = self.host_info[host_name]["handle"]
                    attach_volume = self.sc_api.volume_attach_remote(vol_uuid=self.stripe_uuid,
                                                                     transport=self.transport_type.upper(),
                                                                     remote_ip=self.host_info[host_name]["ip"][0])
                    fun_test.log("Iteration {} - Attach volume API response: {}".format(iteration, attach_volume))
                    fun_test.test_assert(attach_volume["status"],
                                         "Iteration: {} - Attach stripe vol {} over {} for host {}".
                                         format(iteration, self.stripe_uuid, self.transport_type.upper(), host_name))
                    self.nqn = attach_volume["data"]["nqn"]
                    self.detach_uuid = attach_volume["data"]["uuid"]

                    if self.nvme_connect:
                        test_interface = self.host_info[host_name]["test_interface"].name
                        self.pcap_started[iteration][host_name] = False
                        self.pcap_stopped[iteration][host_name] = True
                        self.pcap_pid[iteration][host_name] = {}
                        tcpdump_filename = "/tmp/nvme_connect_iter_{}.pcap".format(iteration)
                        self.pcap_pid[iteration][host_name] = host_handle.tcpdump_capture_start(
                            interface=test_interface, tcpdump_filename=tcpdump_filename, snaplen=1500)
                        if self.pcap_pid[iteration][host_name]:
                            fun_test.log("Iteration: {} - Started packet capture in {}".format(iteration,
                                                                                               host_name))
                            self.pcap_started[iteration][host_name] = True
                            self.pcap_stopped[iteration][host_name] = False
                        else:
                            fun_test.critical("Iteration: {} - Unable to start packet capture in {}".
                                              format(iteration, host_name))

                        if not fun_test.shared_variables["stripe_vol"]["nvme_connect"]:
                            # Checking nvme-connect status
                            if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                                nvme_connect_status = host_handle.nvme_connect(
                                    target_ip=attach_volume["data"]["ip"], nvme_subsystem=self.nqn,
                                    port=self.transport_port, transport=self.transport_type.lower(),
                                    nvme_io_queues=self.nvme_io_queues, hostnqn=self.host_info[host_name]["ip"][0])
                            else:
                                nvme_connect_status = host_handle.nvme_connect(
                                    target_ip=attach_volume["data"]["ip"], nvme_subsystem=self.nqn,
                                    port=self.transport_port, transport=self.transport_type.lower(),
                                    hostnqn=self.host_info[host_name]["ip"][0])

                            if self.pcap_started[iteration][host_name]:
                                host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[iteration][host_name])
                                self.pcap_stopped[iteration][host_name] = True

                            fun_test.test_assert(nvme_connect_status,
                                                 message="Iteration: {} - {} - NVME Connect Status".
                                                 format(iteration, host_name))

                            lsblk_output = host_handle.lsblk("-b")
                            fun_test.simple_assert(lsblk_output, "Listing available volumes")

                            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(
                                self.stripe_details["ns_id"])
                            host_handle.sudo_command("dmesg")
                            lsblk_output = host_handle.lsblk()

                            '''
                            self.host_info[host_name]["nvme_block_device_list"] = []
                            volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                            for volume_name in lsblk_output:
                                match = re.search(volume_pattern, volume_name)
                                if match:
                                    self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                                             str(match.group(2))
                                    if volume_name not in self.nvme_block_device:
                                        self.host_info[host_name]["nvme_block_device_list"].append(
                                            self.nvme_block_device)
                                    fun_test.log("NVMe Block Device/s: {}".
                                                 format(self.host_info[host_name]["nvme_block_device_list"]))

                            try:
                                fun_test.test_assert_expected(
                                    expected=len(self.host_info),
                                    actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                    message="Expected NVMe devices are available")
                            except Exception as ex:
                                fun_test.critical(str(ex))
                            fun_test.log("Iteration: {} - nvme_block_device_list: {}".
                                         format(iteration, self.host_info[host_name]["nvme_block_device_list"]))
                            self.volume_name = self.host_info[host_name]["nvme_block_device_list"][0]

                            '''
                            fun_test.test_assert(self.volume_name in lsblk_output,
                                                 "Iteration: {} - {} device available".format(iteration,
                                                                                              self.volume_name))
                            fun_test.test_assert_expected(expected="disk",
                                                          actual=lsblk_output[self.volume_name]["type"],
                                                          message="Iteration: {} - {} device type check".
                                                          format(iteration, self.volume_name))
                            fun_test.shared_variables["stripe_vol"]["nvme_connect"] = True

                    if self.io_during_attach_detach:
                        wait_time = self.num_hosts - index
                        host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                        # Starting Read for whole volume on first host
                        test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                              func=fio_parser,
                                                                              arg1=host_clone[host_name],
                                                                              host_index=index,
                                                                              filename=test_filename,
                                                                              **self.fio_cmd_args)

                    fun_test.sleep("Iteration: {} - before disconnect".format(iteration), self.nvme_disconn_wait)
                    if self.disconnect_before_detach:
                        try:
                            fun_test.log("Disconnecting volume from the host")
                            # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)  # TODO: SWOS-6165
                            nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)
                            host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                            nvme_disconnect_exit_status = host_handle.exit_status()
                            fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                          message="Iteration: {} - {} - NVME Disconnect Status".
                                                          format(iteration, host_name))
                            fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
                        except Exception as ex:
                            fun_test.critical(str(ex))
                    try:
                        # Detach volume from NVMe-OF controller
                        detach_volume = self.sc_api.detach_volume(port_uuid=self.detach_uuid)
                        fun_test.log("Iteration: {} - Detach volume API response: {}".format(iteration,
                                                                                             detach_volume))
                        fun_test.test_assert(detach_volume, "Iteration: {} - {} - Detach NVMeOF controller".
                                             format(iteration, host_name))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                if self.io_during_attach_detach:
                    # Waiting for all the FIO test threads to complete
                    try:
                        fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                        for index, host_name in enumerate(self.host_info):
                            fio_output[host_name] = {}
                            fun_test.log("Joining fio thread {}".format(index))
                            fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                            if fun_test.shared_variables["fio"][index]:
                                fun_test.add_checkpoint(
                                    "Iteration: {} - FIO output on Disconnect and Detach during an IO on {}".
                                        format(iteration, host_name), "PASSED")
                            else:
                                fun_test.add_checkpoint(
                                    "Iteration: {} - FIO output on Disconnect and Detach during an IO on {}".
                                        format(iteration, host_name), "FAILED")
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fun_test.log("Expected FIO failure {}:\n {}".
                                     format(host_name, fun_test.shared_variables["fio"][index]))
        else:
            for index, host_name in enumerate(self.host_info):
                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                # Starting Read for whole volume on first host
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      **self.fio_cmd_args)
            # Waiting for all the FIO test threads to complete
            try:
                fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                for index, host_name in enumerate(self.host_info):
                    fio_output[host_name] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                           fun_test.shared_variables["fio"][index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))

        fun_test.sleep("Waiting in between iterations", self.iter_interval)

    def cleanup(self):
        try:
            # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                for filename in ["/tmp/nvme_connect.pcap"]:
                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path=filename, target_file_path=pcap_artifact_file)
                fun_test.add_auxillary_file(description="{}: Host {} NVME connect pcap".
                                            format(self.testcase, host_name), filename=pcap_artifact_file)
        except Exception as ex:
            fun_test.critical(str(ex))


class StripedVolAttachConnDisConnDetachIO(StripeVolAttachDetachTestCase):
    def describe(self):
        self.set_test_details(
            id=1,
            summary="Multiple Attach-NvmeConnect-NvmeDisconnect-Detach with IO",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host
                3. Do nvme_connect and perform sequential write and nvme_disconnect and detach
                4. Perform Attach-NvmeConnect- IO With DI -NvmeDisconnect-Disconnect in loop
                5. Start Random Read-Write with data integrity
                ''')

    def setup(self):
        super(StripedVolAttachConnDisConnDetachIO, self).setup()

    def run(self):
        super(StripedVolAttachConnDisConnDetachIO, self).run()

    def cleanup(self):
        super(StripedVolAttachConnDisConnDetachIO, self).cleanup()


class StripedVolAttachConnDisConnDetach(StripeVolAttachDetachTestCase):
    def describe(self):
        self.set_test_details(
            id=2,
            summary="Multiple Attach-NvmeConnect-NvmeDisconnect-Detach without IO",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host
                3. Do nvme_connect and perform sequential write and nvme_disconnect and detach
                4. Perform Attach-NvmeConnect-NvmeDisconnect-Disconnect in loop
                5. Start Random Read-Write with data integrity 
                ''')

    def setup(self):
        super(StripedVolAttachConnDisConnDetach, self).setup()

    def run(self):
        super(StripedVolAttachConnDisConnDetach, self).run()

    def cleanup(self):
        super(StripedVolAttachConnDisConnDetach, self).cleanup()


class StripedVolAttachDetach(StripeVolAttachDetachTestCase):
    def describe(self):
        self.set_test_details(
            id=3,
            summary="Multiple Attach-Detach without IO",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host
                3. Do nvme_connect and perform sequential write and nvme_disconnect and detach
                4. Perform Attach-Disconnect without IO in loop
                5. Start Random Read-Write with data integrity
                ''')

    def setup(self):
        super(StripedVolAttachDetach, self).setup()

    def run(self):
        super(StripedVolAttachDetach, self).run()

    def cleanup(self):
        super(StripedVolAttachDetach, self).cleanup()


if __name__ == "__main__":
    testscript = StripeVolAttachDetachTestScript()
    testscript.add_test_case(StripedVolAttachConnDisConnDetachIO())
    testscript.add_test_case(StripedVolAttachConnDisConnDetach())
    testscript.add_test_case(StripedVolAttachDetach())
    testscript.run()
