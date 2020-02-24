from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.helper import *

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


def deploy_funcp_container(obj, fs_index, update_deploy_script, update_workspace, mode):
    deploy_output = obj.deploy_funcp_container(update_deploy_script=update_deploy_script,
                                                update_workspace=update_workspace, mode=mode)
    fun_test.shared_variables["funcp_deploy"][fs_index] = deploy_output


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(volume, test, num_host, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
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
        self.host_ips = []
        for host_name, host_obj in self.required_hosts.items():
            if host_name not in self.host_info:
                self.host_info[host_name] = {}
            # Retrieving host ips
            if host_name not in self.hosts_test_interfaces:
                self.hosts_test_interfaces[host_name] = []
            test_interface = host_obj.get_test_interface(index=0)
            self.hosts_test_interfaces[host_name].append(test_interface)
            self.host_info[host_name]["test_interface"] = test_interface
            host_ip = self.host_info[host_name]["test_interface"].ip.split('/')[0]
            self.host_ips.append(host_ip)
            self.host_info[host_name]["ip"] = host_ip
            fun_test.log("Host-IP: {}".format(host_ip))
            # Retrieving host handles
            host_instance = host_obj.get_instance()
            self.host_info[host_name]["handle"] = host_instance

        # Rebooting all the hosts in non-blocking mode before the test and getting NUMA cpus
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            if self.override_numa_node["override"]:
                host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
                self.host_info[host_name]["host_numa_cpus"] = host_numa_cpus_filter[self.override_numa_node["override_node"]]
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
        deploy_thread_id = {}
        self.funcp_obj = {}
        self.funcp_spec = {}
        fun_test.shared_variables["funcp_deploy"] = {}
        for index in xrange(self.num_duts):
            self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
            deploy_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=1, obj=self.funcp_obj[index],
                                                                    func=deploy_funcp_container, fs_index=index,
                                                                    update_deploy_script=self.update_deploy_script,
                                                                    update_workspace=self.update_workspace,
                                                                    mode=self.funcp_mode)
        fun_test.log("Deploy Thread IDs: {}".format(deploy_thread_id))
        for index in xrange(self.num_duts):
            try:
                fun_test.log("Joining deploy thread for DUT {}".format(index))
                fun_test.join_thread(fun_test_thread_id=deploy_thread_id[index], sleep_time=1)
                fun_test.log("Deploy Output from DUT {}:\n {}".format(index,
                                                                      fun_test.shared_variables["funcp_deploy"][index]))
            except Exception as ex:
                fun_test.log("Deploy Output from DUT {}:\n {}".format(index,
                                                                      fun_test.shared_variables["funcp_deploy"][index]))
                fun_test.critical(str(ex))
            self.funcp_spec[index] = fun_test.shared_variables["funcp_deploy"][index]
            fun_test.test_assert(self.funcp_spec[index]["status"],
                                 "Starting FunCP docker container in DUT {}".format(index))
            self.funcp_spec[index]["container_names"].sort()

        for index in xrange(self.num_duts):
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
        fun_test.shared_variables["host_ips"] = self.host_ips
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
                fun_test.simple_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(host_name, self.funcp_spec[index / 2]["container_names"][index % 2], ip))

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
                # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
                for host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                    pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path="/tmp/nvme_connect.pcap", target_file_path=pcap_artifact_file)
                    fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                                filename=pcap_artifact_file)

                self.ec_info = fun_test.shared_variables["ec_info"]
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
            self.fs_obj = fun_test.shared_variables["fs_obj"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1_obj = fun_test.shared_variables["f1_obj"]
            self.sc_obj = fun_test.shared_variables["sc_obj"]
            self.f1_ips = fun_test.shared_variables["f1_ips"]
            self.host_info = fun_test.shared_variables["host_info"]
            self.host_ips = fun_test.shared_variables["host_ips"]
            self.num_f1s = fun_test.shared_variables["num_f1s"]
            self.test_network = {}
            self.test_network["f1_loopback_ip"] = self.f1_ips
            self.num_duts = fun_test.shared_variables["num_duts"]
            self.num_hosts = len(self.host_info)

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.ec_info["num_volumes"]:
                for i in range(len(self.host_ips), self.ec_info["num_volumes"]):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(self.host_info[host_name]["ip"])

            initial_nu_stats = {}
            final_nu_stats = {}
            diff_nu_stats = {}
            # Collecting the network related stats from the cconfiguration
            if self.collect_network_stats:
                for index, sc in enumerate(self.sc_obj):
                    if index not in initial_nu_stats:
                        initial_nu_stats[index] = {}
                    initial_nu_stats[index]["peek_psw_global_stats"] = {}
                    initial_nu_stats[index]["peek_vp_packets"] = {}
                    initial_nu_stats[index]["cdu"] = {}
                    initial_nu_stats[index]["ca"] = {}
                    try:
                        initial_nu_stats[index]["peek_psw_global_stats"] = sc.peek_psw_global_stats()
                        initial_nu_stats[index]["peek_vp_packets"] = sc.peek_vp_packets()
                        initial_nu_stats[index]["cdu"] = sc.peek_cdu_stats()
                        initial_nu_stats[index]["ca"] = sc.peek_ca_stats()
                    except Exception as ex:
                        fun_test.critical(str(ex))

            # Creating EC volume
            self.ec_info["storage_controller_list"] = self.sc_obj
            self.ec_info["f1_ips"] = self.f1_ips
            self.ec_info["host_ips"] = self.final_host_ips
            ec_config_status = True
            try:
                (ec_config_status, self.ec_info) = configure_ec_volume_across_f1s(self.ec_info, self.command_timeout)
            except Exception as ex:
                ec_config_status = False
            finally:
                if self.collect_network_stats:
                    for index, sc in enumerate(self.sc_obj):
                        if index not in final_nu_stats:
                            final_nu_stats[index] = {}
                            diff_nu_stats[index] = {}
                        final_nu_stats[index]["peek_psw_global_stats"] = {}
                        final_nu_stats[index]["peek_vp_packets"] = {}
                        final_nu_stats[index]["cdu"] = {}
                        final_nu_stats[index]["ca"] = {}
                        try:
                            final_nu_stats[index]["peek_psw_global_stats"] = sc.peek_psw_global_stats()
                            final_nu_stats[index]["peek_vp_packets"] = sc.peek_vp_packets()
                            final_nu_stats[index]["cdu"] = sc.peek_cdu_stats()
                            final_nu_stats[index]["ca"] = sc.peek_ca_stats()
                        except Exception as ex:
                            fun_test.critical(ex)

                # Stats diff between final stats and initial stats
                diff_nu_stats = get_diff_stats(new_stats=final_nu_stats, old_stats=initial_nu_stats)
                if self.collect_network_stats:
                    for index in xrange(len(self.sc_obj)):
                        fun_test.log("\nStat difference for peek_psw_global_stats at the end of configuration in {} "
                                     "F1 is: \n{}\n".format(index,
                                                            json.dumps(diff_nu_stats[index]["peek_psw_global_stats"],
                                                                       indent=2)))
                        fun_test.log("\nStat difference for peek_vp_packets at the end of configuration in {} F1 is: "
                                     "\n{}\n".format(index, json.dumps(diff_nu_stats[index]["peek_vp_packets"],
                                                                       indent=2)))
                        fun_test.log("\nStat difference for cdu at the end of configuration in {} F1 is: "
                                     "\n{}\n".format(index, json.dumps(diff_nu_stats[index]["cdu"], indent=2)))
                        fun_test.log("\nStat difference for ca at the end of configuration in {} F1 is: "
                                     "\n{}\n".format(index, json.dumps(diff_nu_stats[index]["ca"], indent=2)))
                if not ec_config_status:
                    raise ex

            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            fun_test.shared_variables["ec"]["setup_created"] = True

            # disabling the error_injection for the EC volume
            for index, sc_obj in enumerate(self.sc_obj):
                command_result = {}
                command_result = sc_obj.poke("params/ecvol/error_inject 0", command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT {}".
                                     format(index))

                # Ensuring that the error_injection got disabled properly
                fun_test.sleep("to disable the error_injection", 1)
                command_result = {}
                command_result = sc_obj.peek("params/ecvol", command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.simple_assert(command_result["status"], "Retrieving error_injection status on DUT {}".
                                       format(index))
                fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                              message="Ensuring error_injection got disabled on DUT {}".format(index))

            # Starting packet capture in all the hosts
            pcap_started = {}
            pcap_stopped = {}
            pcap_pid = {}
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                test_interface = self.host_info[host_name]["test_interface"].name
                pcap_started[host_name] = False
                pcap_stopped[host_name] = True
                pcap_pid[host_name] = {}
                pcap_pid[host_name] = host_handle.tcpdump_capture_start(interface=test_interface,
                                                             tcpdump_filename="/tmp/nvme_connect.pcap")
                if pcap_pid[host_name]:
                    fun_test.log("Started packet capture in {}".format(host_name))
                    pcap_started[host_name] = True
                    pcap_stopped[host_name] = False
                else:
                    fun_test.critical("Unable to start packet capture in {}".format(host_name))

            fun_test.shared_variables["fio"] = {}
            for host_name in self.host_info:
                if host_name not in fun_test.shared_variables["ec"]:
                    fun_test.shared_variables["ec"][host_name] = {}
                    fun_test.shared_variables["ec"][host_name]["nvme_connect"] = False
                host_handle = self.host_info[host_name]["handle"]
                host_ip = self.host_info[host_name]["ip"]
                if not fun_test.shared_variables["ec"][host_name]["nvme_connect"]:
                    for sc_index, sc_obj in enumerate(self.sc_obj):
                        if host_ip in self.ec_info[sc_obj]:
                            # Building nvme connect command
                            if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                                    format(self.attach_transport.lower(), self.f1_ips[sc_index],
                                           str(self.transport_port),
                                           self.ec_info[sc_obj][host_ip][self.attach_transport]["nqn"],
                                           self.host_info[host_name]["ip"])
                            else:
                                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                                    format(self.attach_transport.lower(), self.f1_ips[sc_index],
                                           str(self.transport_port),
                                           self.ec_info[sc_obj][host_ip][self.attach_transport]["nqn"],
                                           str(self.io_queues), self.host_info[host_name]["ip"])
                            try:
                                nvme_connect_output = host_handle.sudo_command(command=nvme_connect_cmd, timeout=60)
                                nvme_connect_exit_status = host_handle.exit_status()
                                fun_test.log("nvme_connect_output output is: {}".format(nvme_connect_output))
                                if nvme_connect_exit_status and pcap_started[host_name]:
                                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                                    pcap_stopped[host_name] = True
                            except Exception as ex:
                                # Stopping the packet capture if it is started
                                if pcap_started[host_name]:
                                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                                    pcap_stopped[host_name] = True

                            fun_test.test_assert_expected(expected=0, actual=nvme_connect_exit_status,
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

                    fun_test.test_assert_expected(expected=self.host_info[host_name]["num_volumes"],
                                                  actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                                  message="Expected NVMe devices are available")
                    fun_test.shared_variables["ec"][host_name]["nvme_connect"] = True

                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["fio_filename"] = \
                        ":".join(self.host_info[host_name]["nvme_block_device_list"])
                    fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

            # Stopping the packet capture
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if pcap_started[host_name]:
                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                    pcap_stopped[host_name] = True

            # Setting the syslog level
            for index, sc_obj in enumerate(self.sc_obj):
                command_result = sc_obj.poke(props_tree=["params/syslog/level", self.syslog_level], legacy=False,
                                             command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Setting syslog level to {} in DUT {}".format(self.syslog_level, index))
                command_result = sc_obj.peek(props_tree="params/syslog/level", legacy=False,
                                             command_duration=self.command_timeout)
                fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                              message="Checking syslog level in DUT {}".format(index))

            # Executing the FIO command to fill the volume to it's capacity
            if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
                if self.parallel_warm_up:
                    host_clone = {}
                    warmup_thread_id = {}
                    actual_block_size = int(self.warm_up_fio_cmd_args["bs"].strip("k"))
                    aligned_block_size = int((int(actual_block_size / self.num_hosts) + 3) / 4) * 4
                    self.warm_up_fio_cmd_args["bs"] = str(aligned_block_size) + "k"
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
                            fun_test.join_thread(fun_test_thread_id=warmup_thread_id[index], sleep_time=1)
                            fun_test.log("FIO Command Output: \n{}".format(fun_test.shared_variables["fio"][index]))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    for index, host_name in enumerate(self.host_info):
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                             format(host_name))
                        fun_test.shared_variables["ec"][host_name]["warmup"] = True
                else:
                    for index, host_name in enumerate(self.host_info):
                        host_handle = self.host_info[host_name]["handle"]
                        fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                          cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                          **self.warm_up_fio_cmd_args)
                        fun_test.log("FIO Command Output:\n{}".format(fio_output))
                        fun_test.test_assert(fio_output, "Volume warmup on host {}".format(host_name))

                fun_test.sleep("before actual test",self.iter_interval)
                fun_test.shared_variables["ec"]["warmup_io_completed"] = True

            for index, sc_obj in enumerate(self.sc_obj):
                command_result = sc_obj.poke(props_tree=["params/syslog/level", 6], legacy=False,
                                             command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Setting syslog level to {} in DUT {}".format(6, index))
                command_result = sc_obj.peek(props_tree="params/syslog/level", legacy=False,
                                             command_duration=self.command_timeout)
                fun_test.test_assert_expected(expected=6, actual=command_result["data"],
                                              message="Checking syslog level in DUT {}".format(index))

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Num Hosts", "Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["num_hosts", "block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw",
                           "readbw", "writeclatency", "writelatency90", "writelatency95", "writelatency99",
                           "writelatency9999", "readclatency", "readlatency90", "readlatency95", "readlatency99",
                           "readlatency9999", "fio_job_name"]
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
        aggr_fio_output = {}

        start_stats = True

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}
            fio_job_args = ""
            fio_cmd_args = {}
            mpstat_pid = {}
            mpstat_artifact_file = {}

            test_thread_id = {}
            host_clone = {}

            row_data_dict = {}
            size = (self.ec_info["capacity"] * self.ec_info["num_volumes"]) / (1024 ** 3)
            row_data_dict["size"] = str(size) + "G"
            row_data_dict["num_hosts"] = self.num_hosts

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

            # Computing the interval and duration that the mpstat/vp_util stats needs to be collected
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

            if "bs" in self.fio_cmd_args:
                fio_block_size = self.fio_cmd_args["bs"]
            else:
                fio_block_size = "Mixed"

            if "rw" in self.fio_cmd_args:
                row_data_dict["mode"] = self.fio_cmd_args["rw"]
            else:
                row_data_dict["mode"] = "Combined"

            row_data_dict["block_size"] = fio_block_size

            # Starting the thread to collect the vp_utils stats for the current iteration
            if start_stats:
                pass
                """
                vp_util_post_fix_name = "vp_util_iodepth_{}.txt".format(iodepth)
                vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_post_fix_name)
                stats_thread_id = fun_test.execute_thread_after(time_in_seconds=1, func=collect_vp_utils_stats,
                                                                storage_controller=self.storage_controller,
                                                                output_file=vp_util_artifact_file,
                                                                interval=self.vp_util_args["interval"],
                                                                count=int(mpstat_count), threaded=True)
                """
            else:
                fun_test.critical("Not starting the vp_utils stats collection because of lack of interval and count "
                                  "details")

            for index, host_name in enumerate(self.host_info):
                fio_job_args = ""
                host_handle = self.host_info[host_name]["handle"]
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                host_numa_cpus = self.host_info[host_name]["host_numa_cpus"]
                total_numa_cpus = self.host_info[host_name]["total_numa_cpus"]
                fio_num_jobs = len(nvme_block_device_list)

                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                for vindex, volume_name in enumerate(nvme_block_device_list):
                    fio_job_args += " --name=job{} --filename={}".format(vindex, volume_name)

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
                            if (iodepth / io_factor) <= total_numa_cpus:
                                global_num_jobs = (iodepth / len(nvme_block_device_list)) / io_factor
                                fio_iodepth = io_factor
                                break
                            else:
                                io_factor += 1

                row_data_dict["iodepth"] = int(fio_iodepth) * int(global_num_jobs) * int(fio_num_jobs)
                fun_test.sleep("Waiting in between iterations", self.iter_interval)

                # Calling the mpstat method to collect the mpstats for the current iteration in all the hosts used in
                # the test
                mpstat_cpu_list = self.mpstat_args["cpu_list"]  # To collect mpstat for all CPU's: recommended
                fun_test.log("Collecting mpstat in {}".format(host_name))
                if start_stats:
                    mpstat_post_fix_name = "{}_mpstat_iodepth_{}.txt".format(host_name, row_data_dict["iodepth"])
                    mpstat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=mpstat_post_fix_name)
                    mpstat_pid[host_name] = host_handle.mpstat(cpu_list=mpstat_cpu_list,
                                                                 output_file=self.mpstat_args["output_file"],
                                                                 interval=self.mpstat_args["interval"],
                                                                 count=int(mpstat_count))
                else:
                    fun_test.critical("Not starting the mpstats collection because of lack of interval and count "
                                      "details")

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * global_num_jobs))
                fio_job_name = "{}_iodepth_{}_f1_{}_vol_{}".format(self.fio_job_name, row_data_dict["iodepth"],
                                                                  self.num_f1s, self.ec_info["num_volumes"])
                fun_test.log("fio_job_name used for current iteration: {}".format(fio_job_name))
                if "multiple_jobs" in self.fio_cmd_args:
                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].format(
                        host_numa_cpus, global_num_jobs, fio_iodepth, self.ec_info["capacity"] / global_num_jobs)
                    fio_cmd_args["multiple_jobs"] += fio_job_args
                    fun_test.log("Current FIO args to be used: {}".format(fio_cmd_args))
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename="nofile",
                                                                          timeout=self.fio_cmd_args["timeout"],
                                                                          **fio_cmd_args)
                else:
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
                """
                # Checking whether the vp_util stats collection thread is still running...If so stopping it...
                if fun_test.fun_test_threads[stats_thread_id]["thread"].is_alive():
                    fun_test.critical("VP utilization stats collection thread is still running...Stopping it now")
                    global vp_stats_thread_stop_status
                    vp_stats_thread_stop_status[self.storage_controller] = True
                    fun_test.fun_test_threads[stats_thread_id]["thread"]._Thread__stop()
                """

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

            row_data_dict["fio_job_name"] = fio_job_name

            # Building the table raw for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)
            # post_results("Inspur Performance Test", test_method, *row_data_list)

            # Checking if mpstat process is still running...If so killing it...
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                mpstat_pid_check = host_handle.get_process_id("mpstat")
                if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid[host_name]):
                    host_handle.kill_process(process_id=int(mpstat_pid_check))
                # Saving the mpstat output to the mpstat_artifact_file file
                fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                             source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                             source_file_path=self.mpstat_args["output_file"],
                             target_file_path=mpstat_artifact_file[host_name])
                fun_test.add_auxillary_file(description="Host {} CPU Usage - IO depth {}".
                                            format(host_name, row_data_dict["iodepth"]),
                                            filename=mpstat_artifact_file[host_name])

            """
            # Checking whether the vp_util stats collection thread is still running...If so stopping it...
            if fun_test.fun_test_threads[stats_thread_id]["thread"].is_alive():
                fun_test.critical("VP utilization stats collection thread is still running...Stopping it now")
                global vp_stats_thread_stop_status
                vp_stats_thread_stop_status[self.storage_controller] = True
                fun_test.fun_test_threads[stats_thread_id]["thread"]._Thread__stop()
            fun_test.join_thread(fun_test_thread_id=stats_thread_id, sleep_time=1)
            fun_test.add_auxillary_file(description="F1 VP Utilization - IO depth {}".format(row_data_dict["iodepth"]),
                                        filename=vp_util_artifact_file)
            """

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


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    ecscript.run()
