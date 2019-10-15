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

        come_reboot = False
        if fun_test.shared_variables["setup_created"]:
                self.fs = fun_test.shared_variables["fs"]
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

        command = 'tcpkali '

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

        if not (self.messagerate):
            fun_test.test_assert(False, "tcpkali message rate input is not given")

        if (self.connecttimeout):
            command += '--connect-timeout {} '.format(self.connecttimeout)
        else:
            command += '--connect-timeout 3s '

        if not (self.totalconnection):
            self.totalconnection = [48]
            # self.totalconnection = [int(self.totalconnection / fun_test.shared_variables["num_hosts"])]

        # command += '-c {} '.format(int(self.totalconnection / fun_test.shared_variables["num_hosts"]))

        command += self.testbed_config["dut_info"][str(self.available_dut_indexes[0])]["bond_interface_info"]["0"]["0"]["ip"].split('/')[0]

        # default to NVME reads
        if not self.transport_port:
            self.transport_port = 1099

        command += ":{} ".format(self.transport_port)

        test_thread_id = {}
        host_clone = {}
        fun_test.shared_variables["tcpkali"] = {}
        self.host_info = fun_test.shared_variables["host_info"]

        orignal_cmd = command

        for each_m in self.messagerate:
            for each_c in self.totalconnection:
                aggregate_bw = 0
                command = orignal_cmd
                command += '-r {} '.format(each_m)
                command += '-c {}'.format(each_c)

                for index, host_name in enumerate(self.host_info):
                    host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=0,
                                                                  func=run_tcpkali,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  cmd=command,
                                                                  timeout = self.duration + 60)

                fun_test.sleep("sleep till tcpkali is executed", seconds=self.duration)

                for index, host_name in enumerate(self.host_info):
                    fun_test.log("Joining tcpkali thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("tcpkali Command Output: \n{}".format(fun_test.shared_variables["tcpkali"][index]))

                for index in fun_test.shared_variables["tcpkali"].keys():
                    m = re.search('Aggregate bandwidth:\s+(\d+)\.\d+', fun_test.shared_variables["tcpkali"][index])
                    if m:
                        aggregate_bw += int (m.groups()[0])
                        fun_test.log("aggregate bw on host index {}: {} mbps".format(index, m.groups()[0]))

                    else:
                        fun_test.test_assert(False, "Failed to find aggregated bw for host index: {}".format(index))

                fun_test.log("aggregate bw on all the hosts: {} mbps for  -r {} -c {}".format(aggregate_bw, each_m, each_c))
                fun_test.sleep("sleep 5 seconds for next iteration", seconds=5)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        self.vol_details = fun_test.shared_variables["vol_details"]
        # Checking whether the job's inputs argument is having the list of io_depths to be used in this test.
        # If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_iodepth = job_inputs["io_depth"]

        if not isinstance(self.fio_iodepth, list):
            self.fio_iodepth = [self.fio_iodepth]

        initial_stats = {}
        final_stats = {}
        resultant_stats = {}
        aggregate_resultant_stats = {}
        initial_vol_stat = {}
        final_vol_stat = {}
        initial_rcnvme_stat = {}
        final_rcnvme_stat = {}

        start_stats = True

        try:
            initial_vol_stat[iodepth] = self.storage_controller.peek(
                props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
            fun_test.test_assert(initial_vol_stat[iodepth]["status"], "Volume stats collected before the test")
            fun_test.log("Initial vol stats in script: {}".format(initial_vol_stat[iodepth]))

            initial_rcnvme_stat[iodepth] = self.storage_controller.peek(
                props_tree="storage/devices/nvme/ssds", legacy=False, chunk=8192,
                command_duration=self.command_timeout)
            fun_test.test_assert(initial_rcnvme_stat[iodepth]["status"],
                                 "rcnvme stats collected before the test")
            fun_test.log("Initial rcnvme stats in script: {}".format(initial_rcnvme_stat[iodepth]))
        except Exception as ex:
            fun_test.critical(str(ex))

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

        # Starting the thread to collect the vp_utils stats and resource_bam stats for the current iteration
        if start_stats:
            file_suffix = "iodepth_{}.txt".format(iodepth)
            for index, stat_detail in enumerate(self.stats_collect_details):
                func = stat_detail.keys()[0]
                self.stats_collect_details[index][func]["count"] = int(mpstat_count)
                if func == "vol_stats":
                    self.stats_collect_details[index][func]["vol_details"] = self.vol_details
            fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format(iodepth, self.stats_collect_details))
            self.storage_controller.verbose = False
            self.stats_obj = CollectStats(self.storage_controller)
            self.stats_obj.start(file_suffix, self.stats_collect_details)
            fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format(iodepth, self.stats_collect_details))
        else:
            fun_test.critical("Not starting the vp_utils and resource_bam stats collection because of lack of "
                              "interval and count details")


            # Starting csi perf stats collection if it's set
            if self.csi_perf_enabled:
                if row_data_dict["iodepth"] in self.csi_perf_iodepth:
                    try:
                        fun_test.sleep("for IO to be fully active", 20)
                        csi_perf_obj = CsiPerfTemplate(perf_collector_host_name=str(self.perf_listener_host_name),
                                                       listener_ip=self.perf_listener_ip, fs=self.fs[0],
                                                       listener_port=4420)  # Temp change for testing
                        csi_perf_obj.prepare(f1_index=0)
                        csi_perf_obj.start(f1_index=0, dpc_client=self.storage_controller)
                        fun_test.log("csi perf stats collection is started")
                        # dpcsh_client = self.fs.get_dpc_client(f1_index=0, auto_disconnect=True)
                        fun_test.sleep("Allowing CSI performance data to be collected", 120)
                        csi_perf_obj.stop(f1_index=0, dpc_client=self.storage_controller)
                        fun_test.log("CSI perf stats collection is done")
                    except Exception as ex:
                        fun_test.critical(str(ex))
                else:
                    fun_test.log("Skipping CSI perf collection for current iodepth {}".format(fio_iodepth))
            else:
                fun_test.log("CSI perf collection is not enabled, hence skipping it for current test")





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
                self.stats_obj.stop(self.stats_collect_details)
                self.storage_controller.verbose = True

                if self.cal_amplification:
                    try:
                        final_vol_stat[iodepth] = self.storage_controller.peek(
                            props_tree="storage/volumes", legacy=False, chunk=8192,
                            command_duration=self.command_timeout)
                        fun_test.test_assert(final_vol_stat[iodepth]["status"], "Volume stats collected after the test")
                        fun_test.log("Final vol stats in script: {}".format(final_vol_stat[iodepth]))

                        final_rcnvme_stat[iodepth] = self.storage_controller.peek(
                            props_tree="storage/devices/nvme/ssds", legacy=False, chunk=8192,
                            command_duration=self.command_timeout)
                        fun_test.test_assert(final_rcnvme_stat[iodepth]["status"],
                                             "rcnvme stats collected after the test")
                        fun_test.log("Final rcnvme stats in script: {}".format(final_rcnvme_stat[iodepth]))
                    except Exception as ex:
                        fun_test.critical(str(ex))

            for index, value in enumerate(self.stats_collect_details):
                for func, arg in value.iteritems():
                    filename = arg.get("output_file")
                    if filename:
                        if func == "vp_utils":
                            fun_test.add_auxillary_file(description="F1 VP Utilization - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "per_vp":
                            fun_test.add_auxillary_file(description="F1 Per VP Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "resource_bam_args":
                            fun_test.add_auxillary_file(description="F1 Resource bam stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "vol_stats":
                            fun_test.add_auxillary_file(description="Volume Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "vppkts_stats":
                            fun_test.add_auxillary_file(description="VP Pkts Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "psw_stats":
                            fun_test.add_auxillary_file(description="PSW Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "fcp_stats":
                            fun_test.add_auxillary_file(description="FCP Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "wro_stats":
                            fun_test.add_auxillary_file(description="WRO Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "erp_stats":
                            fun_test.add_auxillary_file(description="ERP Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "etp_stats":
                            fun_test.add_auxillary_file(description="ETP Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "eqm_stats":
                            fun_test.add_auxillary_file(description="EQM Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "hu_stats":
                            fun_test.add_auxillary_file(description="HU Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "ddr_stats":
                            fun_test.add_auxillary_file(description="DDR Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "ca_stats":
                            fun_test.add_auxillary_file(description="CA Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
                        if func == "cdu_stats":
                            fun_test.add_auxillary_file(description="CDU Stats - IO depth {}".
                                                        format(row_data_dict["iodepth"]), filename=filename)
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


                continue

            # Finding the total runtime of the current iteration
            io_runtime = 0
            io_runtime = max(aggr_fio_output[iodepth]["read"]["runtime"], aggr_fio_output[iodepth]["write"]["runtime"])

            row_data_dict["fio_job_name"] = fio_job_name
            if self.cal_amplification:
                '''
                WA = PBW (Physical Bytes Written) / LBW (Logical Bytes Written)
                PBW = Sum of bytes written in each BLT that is member of the Durable volume.
                LBW = Bytes written from the test app.  Should be same as reported by the Top level volume (e.g. LSV).
                '''
                try:
                    if initial_vol_stat[iodepth]["status"] or final_vol_stat[iodepth]["status"]:
                        fun_test.log("\ninitial_vol_stat[{}] is: {}\n".
                                     format(iodepth, initial_vol_stat[iodepth]["data"]))
                        fun_test.log("\nfinal_vol_stat[{}] is: {}\n".format(iodepth, final_vol_stat[iodepth]["data"]))
                        fun_test.log("\nvol_details: {}\n".format(self.vol_details))
                        curr_stats_diff = vol_stats_diff(initial_vol_stats=initial_vol_stat[iodepth]["data"],
                                                         final_vol_stats=final_vol_stat[iodepth]["data"],
                                                         vol_details=self.vol_details)
                        fun_test.simple_assert(curr_stats_diff["status"], "Volume stats diff to measure amplification")
                        fun_test.log("\nVolume stats diff: {}".format(curr_stats_diff))

                        pbw = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LOCAL_THIN"]["write_bytes"]
                        lbw = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LSV"]["write_bytes"]
                        lbw_app = aggr_fio_output[iodepth]['write']["io_bytes"]
                        pbr = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LOCAL_THIN"]["read_bytes"]
                        lbr = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LSV"]["read_bytes"]
                        lbr_app = aggr_fio_output[iodepth]['read']["io_bytes"]

                        fun_test.log("Iodepth: {}\nPhysical Bytes Written from volume stats: {}"
                                     "\nLogical Bytes Written from volume stats: {}\nLogical written bytes by app: {}"
                                     "\nPhysical Bytes Read from volume stats: {}"
                                     "\nLogical Bytes Read from volume stats: {}\nLogical bytes Read by app: {}\n".
                                     format(iodepth, pbw, lbw, lbw_app, pbr, lbr, lbr_app))

                        row_data_dict["write_amp_vol_stats"] = "{0:.2f}".format(divide(n=float(pbw), d=lbw))
                        row_data_dict["write_amp_app_stats"] = "{0:.2f}".format(divide(n=float(pbw), d=lbw_app))
                        row_data_dict["read_amp_vol_stats"] = "{0:.2f}".format(divide(n=float(pbr), d=lbr))
                        row_data_dict["read_amp_app_stats"] = "{0:.2f}".format(divide(n=float(pbr), d=lbr_app))
                        row_data_dict["aggr_amp_vol_stats"] = "{0:.2f}".format(
                            divide(n=float(float(pbw + pbr)), d=(lbw + lbr)))
                        row_data_dict["aggr_amp_app_stats"] = "{0:.2f}".format(
                            divide(n=float(float(pbw + pbr)), d=(lbw_app + lbr_app)))
                except Exception as ex:
                    fun_test.critical(str(ex))

                # Calculating amplification and SSD utilization based on rcnvme stats
                try:
                    if initial_rcnvme_stat[iodepth]["status"] or final_rcnvme_stat[iodepth]["status"]:
                        pbr_rcnvme = 0
                        pbw_rcnvme = 0
                        rcnvme_diff_stats = {}
                        ssd_io_counts = OrderedDict()

                        # Retrieving diff of stats of all ssds
                        rcnvme_diff_stats = get_results_diff(old_result=initial_rcnvme_stat[iodepth]["data"],
                                                             new_result=final_rcnvme_stat[iodepth]["data"])
                        fun_test.simple_assert(rcnvme_diff_stats, "rcnvme diff stats")
                        fun_test.log("\nRCNVMe stats diff: {}".format(rcnvme_diff_stats))

                        # Sum up all rcnvme_read_count & rcnvme_write_count for all the SSD
                        for drive_id in sorted(rcnvme_diff_stats, key=lambda key: int(key)):
                            ssd_io_counts[drive_id] = rcnvme_diff_stats[drive_id]["rcnvme_read_count"] + \
                                                      rcnvme_diff_stats[drive_id]["rcnvme_write_count"]

                        fun_test.log("\nSSD level IO count during the test: {}".format(ssd_io_counts))
                        if io_runtime:
                            for drive_id in ssd_io_counts:
                                key = "SSD{} IOPS".format(drive_id)
                                ssd_util_row_data[key] = ssd_io_counts[drive_id] / io_runtime

                        # Aggregating all ssds read and write bytes stats
                        for i in sorted(rcnvme_diff_stats, key=lambda key: int(key)):
                            pbr_rcnvme += rcnvme_diff_stats[str(i)]["rcnvme_read_bytes"]
                            pbw_rcnvme += rcnvme_diff_stats[str(i)]["rcnvme_write_bytes"]
                        fun_test.log("Iodepth: {}\nPhysical Bytes Written from rcnvme stats: {}\n"
                                     "Physical Bytes Read from rcnvme stats: {}".format(iodepth, pbw_rcnvme,
                                                                                        pbr_rcnvme))

                        row_data_dict["write_amp_rcnvme_stats"] = "{0:.2f}".format(divide(n=float(pbw_rcnvme),
                                                                                          d=lbw_app))
                        row_data_dict["read_amp_rcnvme_stats"] = "{0:.2f}".format(divide(n=float(pbr_rcnvme),
                                                                                         d=lbr_app))
                        row_data_dict["aggr_amp_rcnvme_stats"] = "{0:.2f}".format(
                            divide(n=float(float(pbw_rcnvme + pbr_rcnvme)), d=(lbw_app + lbr_app)))
                except Exception as ex:
                    fun_test.critical(str(ex))

                for key, val in row_data_dict.iteritems():
                    if key.__contains__("_amp_"):
                        fun_test.log("{} is:\t {}".format(key, val))

            # Building the perf row for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)

            # Building the SSD utilization row for this variation
            ssd_util_data_list = []
            for header in ssd_util_headers:
                if header not in ssd_util_row_data:
                    ssd_util_data_list.append(-1)
                else:
                    ssd_util_data_list.append(ssd_util_row_data[header])
            ssd_util_data_rows.append(ssd_util_data_list)

            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Inspur Performance Test", test_method, *row_data_list)

            fun_test.sleep("Waiting in between iterations", self.iter_interval)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

            ssd_util_table_data = {"headers": ssd_util_headers, "rows": ssd_util_data_rows}
            fun_test.add_table(panel_header="SSD Utilization", table_name=self.summary, table_data=ssd_util_table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for iodepth in self.fio_iodepth:
            if not fio_result[iodepth]:
                test_result = False

        fun_test.test_assert(test_result, self.summary)

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
