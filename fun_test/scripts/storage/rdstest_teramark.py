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
Script to run rdstest on F1 from multiple hosts.
'''

def run_tcpkali(arg1, host_index, **kwargs):
    tcpkali_output = arg1.command(command=kwargs['cmd'],
                                  timeout=kwargs['timeout'])
    fun_test.shared_variables["tcpkali"][host_index] = tcpkali_output
    fun_test.simple_assert(tcpkali_output, "tcpkali test for thread {}".format(host_index))
    arg1.disconnect()

def add_to_data_base(value_dict):
    unit_dict = {"input_num_hosts": PerfUnit.UNIT_NUMBER, "input_msg_rate": PerfUnit.UNIT_NUMBER,
                 "input_num_connection": PerfUnit.UNIT_NUMBER, "output_aggregate_bandwidth": PerfUnit.UNIT_MBYTES_PER_SEC}
    # unit_dict_helper = ["num_hosts", "message_rate", "no_of_connection", "aggbw_in_mbps", "rds_job_name"]

    model_name = "RdsClientPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))



class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos  with rdstest
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
            self.disable_wu_watchdog = True
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

        # Set the localip to bond0 ip in the bootargs for rdstest.
        for e, bootarg in enumerate(self.bootargs):
            self.bootargs[e] = re.sub("localip=0.0.0.0", "localip={}".format(
                self.testbed_config["dut_info"][str(self.available_dut_indexes[0])]["bond_interface_info"]["0"]["0"][
                    "ip"].split('/')[0]), bootarg)

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
            self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
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

            # Ensuring perf_host is able to ping F1 IP
            if self.csi_perf_enabled:
                # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
                csi_perf_host_instance = Linux(host_ip=csi_perf_host_obj.spec["host_ip"],
                                               ssh_username=csi_perf_host_obj.spec["ssh_username"],
                                               ssh_password=csi_perf_host_obj.spec["ssh_password"])
                ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                     format(self.perf_listener_host_name, self.csi_f1_ip))

        fun_test.shared_variables["available_dut_indexes"] = self.available_dut_indexes
        fun_test.shared_variables["setup_created"] = True
        fun_test.shared_variables["num_hosts"] = self.num_hosts
        fun_test.shared_variables["testbed_config"] = self.testbed_config

    def cleanup(self):

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
        self.available_dut_indexes = fun_test.shared_variables["available_dut_indexes"]

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False



    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]
        command = 'tcpkali '

        table_data_cols = ["num_hosts", "message_rate", "no_of_connection", "aggbw_in_mbps", "rds_job_name"]
        table_data_rows = []

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]

        if (self.tcpkali_payload):
            command += '-f {} '.format(self.tcpkali_payload)
        else:
            fun_test.test_assert(False, "payload path is not given")

        command += '--latency-first-byte '

        if (self.duration):
            command += '-T {} '.format(self.duration)
        else:
            self.duration = 60
            command += '-T 60 '

        if not hasattr(self, "messagerate"):
            fun_test.test_assert(False, "tcpkali message rate input is not given")

        if (self.connecttimeout):
            command += '--connect-timeout {} '.format(self.connecttimeout)
        else:
            command += '--connect-timeout 3s '

        if not hasattr(self, "totalconnection"):
            self.totalconnection = [48]
            # self.totalconnection = [int(self.totalconnection / fun_test.shared_variables["num_hosts"])]

        # command += '-c {} '.format(int(self.totalconnection / fun_test.shared_variables["num_hosts"]))

        command += fun_test.shared_variables["f1_ips"][0]
        # command += self.testbed_config["dut_info"][str(self.available_dut_indexes[0])]["bond_interface_info"]["0"]["0"]["ip"].split('/')[0]

        # default to NVME reads
        if not self.transport_port:
            self.transport_port = 1099

        command += ":{} ".format(self.transport_port)

        start_stats = False

        if hasattr(self, "start_stats"):
            if self.start_stats == True:
                start_stats = True
            else:
                start_stats = False
        else:
            start_stats = False

        test_thread_id = {}
        host_clone = {}
        fun_test.shared_variables["tcpkali"] = {}
        self.host_info = fun_test.shared_variables["host_info"]

        orignal_cmd = command

        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]

        row_data_dict = {}

        headers = ["num_hosts", "message_rate", "no_of_connection", "aggbw_in_mbps", "rds_job_name"]

        for each_m in self.messagerate:
            for each_c in self.totalconnection:
                aggregate_bw = 0
                command = orignal_cmd
                command += '-r {} '.format(each_m)
                command += '-c {}'.format(each_c)

                row_data_dict['message_rate'] = each_m
                row_data_dict['no_of_connection'] = each_c
                row_data_dict['num_hosts'] = len(self.host_info)
                row_data_dict['rds_job_name'] = "RDS_client_test_{}_hosts_{}_messagerate_{}_noofconn_aggbw".format(len(self.host_info), each_m, each_c)

                # Starting the thread to collect the vp_utils stats and resource_bam stats for the current iteration
                if start_stats:
                    file_suffix = "message_{}_conn_{}.txt".format(each_m, each_c)
                    for index, stat_detail in enumerate(self.stats_collect_details):
                        func = stat_detail.keys()[0]
                        self.stats_collect_details[index][func]["count"] = int(self.duration / self.stats_collect_details[index][func]["interval"])
                    fun_test.log("Different stats collection thread details for messagerate {} and total connection {} before starting them".format(each_m, each_c, self.stats_collect_details))
                    self.storage_controller.verbose = False
                    self.stats_obj = CollectStats(self.storage_controller)
                    self.stats_obj.start(file_suffix, self.stats_collect_details)
                    fun_test.log("Different stats collection thread details for messagerate {} and total connection {} after starting them".format(each_m, each_c, self.stats_collect_details))
                else:
                    fun_test.critical("Not starting the vp_utils and resource_bam stats collection because of lack of "
                                      "interval and count details")

                try:
                    for index, host_name in enumerate(self.host_info):
                        host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                        test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=0,
                                                                  func=run_tcpkali,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  cmd=command,
                                                                  timeout = self.duration + 60)

                    for index, host_name in enumerate(self.host_info):
                        fun_test.log("Joining tcpkali thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                        fun_test.log("tcpkali Command Output: \n{}".format(fun_test.shared_variables["tcpkali"][index]))

                except Exception as ex:
                    fun_test.critical(str(ex))
                finally:
                    self.stats_obj.stop(self.stats_collect_details)
                    self.storage_controller.verbose = True

                for index, value in enumerate(self.stats_collect_details):
                    for func, arg in value.iteritems():
                        filename = arg.get("output_file")
                        if filename:
                            if func == "vp_utils":
                                fun_test.add_auxillary_file(description="F1 VP Utilization - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "per_vp":
                                fun_test.add_auxillary_file(description="F1 Per VP Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "resource_bam_args":
                                fun_test.add_auxillary_file(description="F1 Resource bam stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "vol_stats":
                                fun_test.add_auxillary_file(description="Volume Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "vppkts_stats":
                                fun_test.add_auxillary_file(description="VP Pkts Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "psw_stats":
                                fun_test.add_auxillary_file(description="PSW Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "fcp_stats":
                                fun_test.add_auxillary_file(description="FCP Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "wro_stats":
                                fun_test.add_auxillary_file(description="WRO Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "erp_stats":
                                fun_test.add_auxillary_file(description="ERP Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "etp_stats":
                                fun_test.add_auxillary_file(description="ETP Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "eqm_stats":
                                fun_test.add_auxillary_file(description="EQM Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "hu_stats":
                                fun_test.add_auxillary_file(description="HU Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "ddr_stats":
                                fun_test.add_auxillary_file(description="DDR Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "ca_stats":
                                fun_test.add_auxillary_file(description="CA Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)
                            if func == "cdu_stats":
                                fun_test.add_auxillary_file(description="CDU Stats - message_{}_conn_{}.txt".format(each_m, each_c), filename=filename)

                for index in fun_test.shared_variables["tcpkali"].keys():
                    m = re.search('Aggregate bandwidth:\s+(\d+)\.\d+', fun_test.shared_variables["tcpkali"][index])
                    if m:
                        aggregate_bw += int (m.groups()[0])
                        fun_test.log("aggregate bw on host index {}: {} mbps".format(index, m.groups()[0]))

                    else:
                        fun_test.test_assert(False, "Failed to find aggregated bw for host index: {}".format(index))

                fun_test.log("aggregate bw on all the hosts: {} mbps for  -r {} -c {}".format(aggregate_bw, each_m, each_c))
                fun_test.sleep("sleep 5 seconds for next iteration", seconds=5)

                row_data_dict['aggbw_in_mbps'] = aggregate_bw

                data = [each_m, each_c, len(self.host_info), aggregate_bw]

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)

                table_data = {"headers": headers, "rows": table_data_rows}
                fun_test.add_table(panel_header="RDS TEST perf table", table_name="RDS TEST for {} message {} connections and {} no of hosts".format(each_m, each_c, len(self.host_info)), table_data=table_data)

                # Datetime required for daily Dashboard data filter
                try:
                    # Building value_dict for dashboard update
                    value_dict = {
                        "date_time": self.db_log_time,
                        "platform": FunPlatform.F1,
                        "version": fun_test.get_version(),
                        "num_f1s": self.num_f1s,
                        "input_num_hosts": len(self.host_info),
                        "input_msg_rate": each_m,
                        "input_num_connection": each_c,
                        "output_aggregate_bandwidth": aggregate_bw
                        }
                    if self.post_results:
                        fun_test.log("Posting results on dashboard")
                        add_to_data_base(value_dict)
                except Exception as ex:
                    fun_test.critical(str(ex))
    def cleanup(self):
        self.stats_obj.stop(self.stats_collect_details)
        self.storage_controller.verbose = True


class rdsteramarktest(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="rdstest for funos",
                              steps="""
        1. Bring up FS with rdstest app 
        2. run tcpkali from hosts and collect perf.
        """)

    def setup(self):
        super(rdsteramarktest, self).setup()

    def run(self):
        super(rdsteramarktest, self).run()

    def cleanup(self):
        super(rdsteramarktest, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(rdsteramarktest())
    ecscript.run()
