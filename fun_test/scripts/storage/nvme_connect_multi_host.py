from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from storage_helper import *
from collections import OrderedDict
import re

'''
script to verify fix for nvme connect swos-5844 issue
'''


class MultiHostVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        fun_test.shared_variables["fio"] = {}

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = 2
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
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = True

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
            self.required_hosts = self.topology_helper.get_available_hosts()
            self.testbed_config = self.topology_helper.spec
            self.total_available_duts = len(self.available_dut_indexes)

        fun_test.test_assert(expression=self.num_duts <= self.total_available_duts,
                             message="Testbed has enough DUTs")

        for i in range(len(self.bootargs)):
            self.bootargs[i] += " --mgmt"
            if self.disable_wu_watchdog:
                self.bootargs[i] += " --disable-wu-watchdog"

        # Deploying of DUTs
        for dut_index in self.available_dut_indexes:
            self.topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]},
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

        self.hosts_test_interfaces = {}
        self.host_handles = {}
        self.host_ips = []
        self.host_numa_cpus = {}
        self.total_numa_cpus = {}
        for host_name, host_obj in self.required_hosts.items():
            # Retrieving host ips
            # test_interfaces = host.get_test_interfaces()
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
        self.fs_objs = []
        self.fs_spec = []
        self.come_obj = []
        self.f1_objs = {}
        self.sc_objs = []
        self.f1_ips = []
        self.gateway_ips = []
        for curr_index, dut_index in enumerate(self.available_dut_indexes):
            self.fs_objs.append(self.topology.get_dut_instance(index=dut_index))
            self.fs_spec.append(self.topology.get_dut(index=dut_index))
            self.come_obj.append(self.fs_objs[curr_index].get_come())
            self.f1_objs[curr_index] = []
            for j in xrange(self.num_f1_per_fs):
                self.f1_objs[curr_index].append(self.fs_objs[curr_index].get_f1(index=j))
                self.sc_objs.append(self.f1_objs[curr_index][j].get_dpc_storage_controller())

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
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog_level"] = self.syslog
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

        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        come_reboot = False
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]

                # Deleting the volumes
                for i in range(0, fun_test.shared_variables["blt_count"], 1):

                    lun_uuid = fun_test.shared_variables["thin_uuid"][i]

                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[i], ns_id=1, command_duration=self.command_timeout)

                    fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

                    command_result = self.storage_controller.delete_volume(uuid=lun_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, lun_uuid))

                    # Deleting the controller
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Storage Controller Delete")

            except:
                fun_test.log("Clean-up of volumes failed.")

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

        fun_test.log("FS cleanup")
        for fs in fun_test.shared_variables["fs_objs"]:
            fs.cleanup()

        # self.storage_controller.disconnect()
        self.topology.cleanup()  # Why is this needed?


class MultiHostVolumePerformanceTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

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

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12
        if not hasattr(self, "no_of_nvme_connect"):
            self.no_of_nvme_connect = 10

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog_level"]
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]) \
                and (not fun_test.shared_variables["blt"]["warmup_done"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # Create BLT's
            self.vol_list = []
            self.thin_uuid_list = []

            for i in range(0, self.blt_count):
                vol_details = {}
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                vol_details["vol_uuid"] = cur_uuid
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_details["capacity"],
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i + 1),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} on DUT".format(i + 1, cur_uuid))
                # self.nvme_block_device.append(vol_details["name"])

                self.vol_list.append(vol_details)

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

            # Create TCP controllers (1 for each SSD and Host)
            self.nvme_block_device = []
            self.ctrlr_uuid = []
            for i in range(0, self.blt_count):
                ctrl_details = {}
                cur_uuid = utils.generate_uuid()
                nqn = "nqn" + str(i + 1)
                self.ctrlr_uuid.append(cur_uuid)
                self.vol_list[i]["ctrl_uuid"] = cur_uuid
                self.vol_list[i]["nqn"] = nqn
                command_result = self.storage_controller.create_controller(
                    ctrlr_uuid=cur_uuid,
                    transport=unicode.upper(self.transport_type),
                    remote_ip=self.host_ips[i],
                    nqn=nqn,
                    port=self.transport_port,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating controller for {} with uuid {} on DUT".
                                     format(self.transport_type, cur_uuid))

                # Attach controller to BLTs
                ns_id = 1  # ns_id is 1 since there is 1 vol per controller
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=cur_uuid,
                                                                                     vol_uuid=self.vol_list[i][
                                                                                         "vol_uuid"],
                                                                                     ns_id=ns_id,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                     format(self.thin_uuid_list[i], cur_uuid))
                self.vol_list[i]["vol_name"] = self.nvme_device + "n" + str(ns_id)
                self.nvme_block_device.append(self.vol_list[i]["vol_name"])
                self.vol_list[i]["ns_id"] = ns_id

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nvme_block_device_list"] = self.nvme_block_device

            # Setting the syslog level to 6
            command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

            command_result = self.storage_controller.peek("params/syslog/level")
            fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                          message="Checking syslog level")

            for conn_no in range(1, self.no_of_nvme_connect + 1):

                for i in range(0, self.blt_count):
                    key = self.host_ips[i]
                    nqn = self.vol_list[i]["nqn"]

                    hostname = str(self.host_handles[key]).split()[1]

                    if conn_no == 1:

                        self.host_handles[key].sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                        self.host_handles[key].sudo_command("/etc/init.d/irqbalance stop")
                        irq_bal_stat = self.host_handles[key].command("/etc/init.d/irqbalance status")

                        if "dead" in irq_bal_stat:
                            fun_test.log("IRQ balance stopped on {}".format(i))
                        else:
                            fun_test.log("IRQ balance not stopped on {}".format(i))
                            install_status = self.host_handles[key].install_package("tuned")
                            fun_test.test_assert(install_status, "tuned installed successfully")

                            self.host_handles[key].sudo_command(
                                "tuned-adm profile network-throughput && tuned-adm active")

                        command_result = self.host_handles[key].command("lsmod | grep -w nvme")
                        if "nvme" in command_result:
                            fun_test.log("nvme driver is loaded")
                        else:
                            fun_test.log("Loading nvme")
                            self.host_handles[key].modprobe("nvme")
                            self.host_handles[key].modprobe("nvme_core")
                        command_result = self.host_handles[key].lsmod("nvme_tcp")
                        if "nvme_tcp" in command_result:
                            fun_test.log("nvme_tcp driver is loaded")
                        else:
                            fun_test.log("Loading nvme_tcp")
                            self.host_handles[key].modprobe("nvme_tcp")
                            self.host_handles[key].modprobe("nvme_fabrics")

                    pcap_file = "/tmp/SWOS-5844-{}_nvme_connect_auto_{}.pcap".format(hostname, conn_no)

                    pcap_pid = self.host_handles[key].tcpdump_capture_start(interface="enp216s0",
                                                                            tcpdump_filename=pcap_file, snaplen=1500)
                    nvme_connect_failed = False

                    try:
                        if hasattr(self, "nvme_io_q"):
                            command_result = self.host_handles[key].sudo_command(
                                "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                                    unicode.lower(self.transport_type),
                                    self.test_network["f1_loopback_ip"],
                                    self.transport_port,
                                    nqn,
                                    self.nvme_io_q,
                                    self.host_ips[i]), timeout=60)
                            fun_test.log(command_result)
                        else:
                            command_result = self.host_handles[key].sudo_command(
                                "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                                    self.test_network["f1_loopback_ip"],
                                                                                    self.transport_port,
                                                                                    nqn,
                                                                                    self.host_ips[i]), timeout=60)
                    except:
                        nvme_connect_failed = True
                        fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed,
                                                                                                    pcap_file))
                    fun_test.log(command_result)

                    fun_test.sleep("Wait for couple of seconds before taking tcpdump", 2)

                    pcap_artifact_file = fun_test.get_test_case_artifact_file_name(
                        post_fix_name="{}".format(pcap_file.split('/')[-1]))

                    self.host_handles[key].tcpdump_capture_stop(process_id=pcap_pid)

                    if not nvme_connect_failed:
                        fun_test.log(
                            "nvme connect on host {} for iteration {} is successful".format(hostname, conn_no))
                        if conn_no == 1:
                            fun_test.scp(source_port=self.host_handles[key].ssh_port,
                                         source_username=self.host_handles[key].ssh_username,
                                         source_password=self.host_handles[key].ssh_password,
                                         source_ip=self.host_handles[key].host_ip,
                                         source_file_path=pcap_file,
                                         target_file_path=pcap_artifact_file)
                            fun_test.add_auxillary_file(
                                description="Host {} NVME connect passed pcap".format(hostname),
                                filename=pcap_artifact_file)

                    else:
                        fun_test.log(
                            "nvme connect on host {} failed on iteration: {}. Check pcap file {} for errors".format(
                                hostname, conn_no, pcap_file))
                        fun_test.scp(source_port=self.host_handles[key].ssh_port,
                                     source_username=self.host_handles[key].ssh_username,
                                     source_password=self.host_handles[key].ssh_password,
                                     source_ip=self.host_handles[key].host_ip,
                                     source_file_path=pcap_file,
                                     target_file_path=pcap_artifact_file)
                        fun_test.add_auxillary_file(
                            description="Host {} NVME connect failed pcap".format(hostname),
                            filename=pcap_artifact_file)

                    fun_test.test_assert(expression=not nvme_connect_failed,
                                         message="SWOS-5844: nvme connect passed on host {}".format(hostname))

                for i in range(0, self.blt_count):
                    key = self.host_ips[i]
                    nqn = self.vol_list[i]["nqn"]
                    command_result = self.host_handles[key].sudo_command("nvme disconnect -n {}".format(nqn))
                    fun_test.log(command_result)

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):
        pass

    def cleanup(self):
        pass


class MultiNvmeConnect(MultiHostVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect no of hosts with one blt each"
                                      "and issue nvme connect disconnect continously until hit the issue",
                              steps='''
        1. Create 1 BLT volumes fro each host
        2. Create a storage controller for TCP and attach above volumes to this controller. Strt TCPDUMP
        3. Do NVME connect from each host see if you are hitting swos-5844.
        4. If pass disconnect and do for next iteration. if fails stop TCPDUMP and collect the logs
        ''')

    def run(self):
        pass


if __name__ == "__main__":
    bltscript = MultiHostVolumePerformanceScript()
    bltscript.add_test_case(MultiNvmeConnect())
    bltscript.run()
