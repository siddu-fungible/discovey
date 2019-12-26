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
from threading import Lock
from lib.templates.storage.storage_controller_api import *

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(volume, test, num_host, block_size, io_depth, size, operation, write_iops, read_iops, write_bw,
                 read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name,
                 write_amp_vol_stats, read_amp_vol_stats, aggr_amp_vol_stats, write_amp_app_stats, read_amp_app_stats,
                 aggr_amp_app_stats, write_amp_rcnvme_stats, read_amp_rcnvme_stats, aggr_amp_rcnvme_stats):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name", "write_amp_vol_stats", "read_amp_vol_stats",
              "aggr_amp_vol_stats", "write_amp_app_stats", "read_amp_app_stats", "aggr_amp_app_stats",
              "write_amp_rcnvme_stats", "read_amp_rcnvme_stats", "aggr_amp_rcnvme_stats"]:
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
            self.syslog = "default"
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
            self.syslog = job_inputs["syslog"]

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
            self.csi_cache_miss_enabled = fun_test.get_job_environment_variable("csi_cache_miss")
            fun_test.log("csi_perf_enabled is set as: {} for current run".format(self.csi_perf_enabled))
            fun_test.log("csi_cache_miss_enabled is set as: {} for current run".format(self.csi_cache_miss_enabled))

            if self.csi_perf_enabled or self.csi_cache_miss_enabled:
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
                if self.csi_perf_enabled:
                    self.bootargs[0] += " --perf csi-local-ip={} csi-remote-ip={} pdtrace-hbm-size-kb={}".format(
                        self.csi_f1_ip, self.perf_listener_ip, self.csi_perf_pdtrace_hbm_size_kb)
                elif self.csi_cache_miss_enabled:
                    self.bootargs[0] += " --csi-cache-miss csi-local-ip={} csi-remote-ip={} pdtrace-hbm-size-kb={}".format(
                        self.csi_f1_ip, self.perf_listener_ip, self.csi_perf_pdtrace_hbm_size_kb)

            self.tftp_image_path = fun_test.get_job_environment_variable("tftp_image_path")
            self.bundle_image_parameters = fun_test.get_job_environment_variable("bundle_image_parameters")

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
                if host_name.startswith("cab0"):
                    if self.override_numa_node["override"]:
                        host_numa_cpus_filter = host_handle.lscpu("node[01]")
                        self.host_info[host_name]["host_numa_cpus"] = ",".join(host_numa_cpus_filter.values())
                else:
                    if self.override_numa_node["override"]:
                        host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
                        self.host_info[host_name]["host_numa_cpus"] = host_numa_cpus_filter[
                            self.override_numa_node["override_node"]]
                    else:
                        self.host_info[host_name]["host_numa_cpus"] = fetch_numa_cpus(host_handle,
                                                                                      self.ethernet_adapter)

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
            self.funcp_obj[0] = StorageFsTemplate(self.come_obj[0])
            if self.bundle_image_parameters:
                fun_test.log("Bundle image installation")
                if self.install == "fresh":
                    # For fresh install, cleanup cassandra DB by restarting run_sc container with cleanup
                    fun_test.log("Bundle Image boot: It's a fresh install. Cleaning up the database")
                    path = "{}/{}".format(self.sc_script_dir, self.run_sc_script)
                    if self.come_obj[0].check_file_directory_exists(path=path):
                        self.come_obj[0].command("cd {}".format(self.sc_script_dir))
                        # Restarting run_sc with -c option
                        self.come_obj[0].command("sudo ./{} -c restart".format(self.run_sc_script),
                                                 timeout=self.run_sc_restart_timeout)
                        fun_test.test_assert_expected(
                            expected=0, actual=self.come_obj[0].exit_status(),
                            message="Bundle Image boot: Fresh Install: run_sc: restarted with cleanup")
                        # Check if run_sc container is running
                        run_sc_status_cmd = "docker ps -a --format '{{.Names}}' | grep run_sc"
                        timer = FunTimer(max_time=self.container_up_timeout)
                        while not timer.is_expired():
                            run_sc_name = self.come_obj[0].command(
                                run_sc_status_cmd, timeout=self.command_timeout).split("\n")[0]
                            if run_sc_name:
                                fun_test.log("Bundle Image boot: Fresh Install: run_sc: Container is up and running")
                                break
                            else:
                                fun_test.sleep("for the run_sc docker container to start", 1)
                                fun_test.log("Remaining Time: {}".format(timer.remaining_time()))
                        else:
                            fun_test.critical(
                                "Bundle Image boot: Fresh Install: run_sc container is not restarted within {} seconds "
                                "after cleaning up the DB".format(self.container_up_timeout))
                            fun_test.test_assert(
                                False, "Bundle Image boot: Fresh Install: Cleaning DB and restarting run_sc container")

                self.funcp_spec[0] = self.funcp_obj[0].get_container_objs()
                self.funcp_spec[0]["container_names"].sort()
                # Ensuring run_sc is still up and running because after restarting run_sc with cleanup,
                # chances are that it may die within few seconds after restart
                run_sc_status_cmd = "docker ps -a --format '{{.Names}}' | grep run_sc"
                run_sc_name = self.come_obj[0].command(run_sc_status_cmd, timeout=self.command_timeout).split("\n")[0]
                fun_test.simple_assert(run_sc_name, "Bundle Image boot: run_sc: Container is up and running")

                # Declaring SC API controller
                self.sc_api = StorageControllerApi(api_server_ip=self.come_obj[0].host_ip,
                                                   api_server_port=self.api_server_port,
                                                   username=self.api_server_username,
                                                   password=self.api_server_password)

                # Polling for API Server status
                api_server_up_timer = FunTimer(max_time=self.api_server_up_timeout)
                while not api_server_up_timer.is_expired():
                    api_server_response = self.sc_api.get_api_server_health()
                    if api_server_response["status"]:
                        fun_test.log("Bundle Image boot: API server is up and running")
                        break
                    else:
                        fun_test.sleep("waiting for API server to be up", 10)
                        fun_test.log("Remaining Time: {}".format(api_server_up_timer.remaining_time()))
                fun_test.simple_assert(expression=not api_server_up_timer.is_expired(),
                                       message="Bundle Image boot: API server is up")
                fun_test.sleep("Bundle Image boot: waiting for API server to be ready", 60)
                # Check if bond interface status is Up and Running
                for f1_index, container_name in enumerate(self.funcp_spec[0]["container_names"]):
                    if container_name == "run_sc":
                        continue
                    bond_interfaces_status = self.funcp_obj[0].is_bond_interface_up(container_name=container_name,
                                                                                    name="bond0")
                    # If bond interface is still not in UP and RUNNING state, flip it
                    if not bond_interfaces_status:
                        fun_test.log("Bundle Image boot: bond0 interface is not up in speculated time, flipping it..")
                        bond_interfaces_status = self.funcp_obj[0].is_bond_interface_up(
                            container_name=container_name, name="bond0", flip_interface=True)
                    fun_test.test_assert_expected(expected=True, actual=bond_interfaces_status,
                                                  message="Bundle Image boot: Bond Interface is Up & Running")
                # If fresh install, configure dataplane ip as database is cleaned up
                if self.install == "fresh":
                    # Getting all the DUTs of the setup
                    nodes = self.sc_api.get_dpu_ids()
                    fun_test.test_assert(nodes, "Bundle Image boot: Getting UUIDs of all DUTs in the setup")
                    for node_index, node in enumerate(nodes):
                        # Extracting the DUT's bond interface details
                        ip = self.fs_spec[node_index / 2].spec["bond_interface_info"][str(node_index % 2)][str(0)]["ip"]
                        ip = ip.split('/')[0]
                        subnet_mask = self.fs_spec[node_index / 2].spec["bond_interface_info"][
                            str(node_index % 2)][str(0)]["subnet_mask"]
                        route = self.fs_spec[node_index / 2].spec["bond_interface_info"][str(node_index % 2)][
                            str(0)]["route"][0]
                        next_hop = "{}/{}".format(route["gateway"], route["network"].split("/")[1])
                        self.f1_ips.append(ip)

                        fun_test.log(
                            "Bundle Image boot: Current {} node's bond0 is going to be configured with {} IP address "
                            "with {} subnet mask with next hop set to {}".format(node, ip, subnet_mask, next_hop))
                        # Configuring Dataplane IP
                        result = self.sc_api.configure_dataplane_ip(
                            dpu_id=node, interface_name="bond0", ip=ip, subnet_mask=subnet_mask, next_hop=next_hop,
                            use_dhcp=False)
                        fun_test.log(
                            "Bundle Image boot: Dataplane IP configuration result of {}: {}".format(node, result))
                        fun_test.test_assert(
                            result["status"],
                            "Bundle Image boot: Configuring {} DUT with Dataplane IP {}".format(node, ip))
                else:
                    # TODO: Retrieve the dataplane IP and validate if dataplane ip is same as bond interface ip
                    pass
            elif self.tftp_image_path:
                fun_test.log("TFTP image installation")
                # Check the init-fs1600 service is running
                # If so check all the required dockers are running
                # else fallback to legacy by disabling the servicing, killing health check and the left over containers
                # expected_containers_up = False
                # init_fs1600_service_status = False
                fun_test.simple_assert(init_fs1600_status(self.come_obj[0]),
                                       "TFTP image boot: init-fs1600 service status: enabled")
                # init-fs1600 service is enabled, checking if all the required containers are running
                # init_fs1600_service_status = True
                expected_containers = ['F1-0', 'F1-1', 'run_sc']
                container_chk_timer = FunTimer(max_time=(self.container_up_timeout * 2))
                while not container_chk_timer.is_expired():
                    container_names = self.funcp_obj[0].get_container_names(
                        stop_run_sc=False, include_storage=True)['container_name_list']
                    if all(container in container_names for container in expected_containers):
                        # expected_containers_up = True
                        fun_test.log("TFTP image boot: init-fs1600 enabled: Expected containers are up and running")
                        break
                    else:
                        fun_test.sleep(
                            "TFTP image boot: init-fs1600 enabled: waiting for expected containers to show up", 10)
                        fun_test.log("Remaining Time: {}".format(container_chk_timer.remaining_time()))
                # Asserting if expected containers are not UP status
                fun_test.simple_assert(not container_chk_timer.is_expired(),
                                       "TFTP image boot: init-fs1600 enabled: Expected containers are running")
                # Cleaning up DB by restarting run_sc.py script with -c option
                if self.install == "fresh":
                    fun_test.log("TFTP image boot: init-fs1600 enabled: It's a fresh install. Cleaning up the database")
                    path = "{}/{}".format(self.sc_script_dir, self.run_sc_script)
                    if self.come_obj[0].check_file_directory_exists(path=path):
                        self.come_obj[0].command("cd {}".format(self.sc_script_dir))
                        # restarting run_sc with -c option
                        self.come_obj[0].command("sudo ./{} -c restart".format(self.run_sc_script),
                                                 timeout=self.run_sc_restart_timeout)
                        fun_test.test_assert_expected(
                            expected=0, actual=self.come_obj[0].exit_status(),
                            message="TFTP Image boot: init-fs1600 enabled: Fresh Install: run_sc: "
                                    "restarted with cleanup")
                        # Check if run_sc container is up and running
                        run_sc_status_cmd = "docker ps -a --format '{{.Names}}' | grep run_sc"
                        timer = FunTimer(max_time=self.container_up_timeout)
                        while not timer.is_expired():
                            run_sc_name = self.come_obj[0].command(
                                run_sc_status_cmd, timeout=self.command_timeout).split("\n")[0]
                            if run_sc_name:
                                fun_test.log("TFTP Image boot: init-fs1600 enabled: Fresh Install: run_sc: "
                                             "Container is up and running")
                                break
                            else:
                                fun_test.sleep("for the run_sc docker container to start", 1)
                                fun_test.log("Remaining Time: {}".format(timer.remaining_time()))
                        else:
                            fun_test.critical(
                                "TFTP Image boot: init-fs1600 enabled: Fresh Install: run_sc container is not "
                                "restarted within {} seconds after cleaning up the DB".format(
                                    self.container_up_timeout))
                            fun_test.test_assert(False, "TFTP Image boot: init-fs1600 enabled: Fresh Install: "
                                                        "Cleaning DB and restarting run_sc container")

                        self.funcp_spec[0] = self.funcp_obj[0].get_container_objs()
                        self.funcp_spec[0]["container_names"].sort()
                        # Ensuring run_sc is still up and running because after restarting run_sc with cleanup,
                        # chances are that it may die within few seconds after restart
                        run_sc_status_cmd = "docker ps -a --format '{{.Names}}' | grep run_sc"
                        run_sc_name = self.come_obj[0].command(run_sc_status_cmd,
                                                               timeout=self.command_timeout).split("\n")[0]
                        fun_test.simple_assert(run_sc_name, "TFTP Image boot: init-fs1600 enabled: run_sc: "
                                                            "Container is up and running")

                        # Declaring SC API controller
                        self.sc_api = StorageControllerApi(api_server_ip=self.come_obj[0].host_ip,
                                                           api_server_port=self.api_server_port,
                                                           username=self.api_server_username,
                                                           password=self.api_server_password)

                        # Polling for API Server status
                        api_server_up_timer = FunTimer(max_time=self.api_server_up_timeout)
                        while not api_server_up_timer.is_expired():
                            api_server_response = self.sc_api.get_api_server_health()
                            if api_server_response["status"]:
                                fun_test.log(
                                    "TFTP Image boot: init-fs1600 enabled: API server is up and running")
                                break
                            else:
                                fun_test.sleep(" waiting for API server to be up", 10)
                                fun_test.log("Remaining Time: {}".format(api_server_up_timer.remaining_time()))
                        fun_test.simple_assert(expression=not api_server_up_timer.is_expired(),
                                               message="TFTP Image boot: init-fs1600 enabled: API server is up")
                        fun_test.sleep(
                            "TFTP Image boot: init-fs1600 enabled: waiting for API server to be ready", 60)
                        # Check if bond interface status is Up and Running
                        for f1_index, container_name in enumerate(self.funcp_spec[0]["container_names"]):
                            if container_name == "run_sc":
                                continue
                            bond_interfaces_status = self.funcp_obj[0].is_bond_interface_up(
                                container_name=container_name,
                                name="bond0")
                            # If bond interface is still not in UP and RUNNING state, flip it
                            if not bond_interfaces_status:
                                fun_test.log("TFTP Image boot: init-fs1600 enabled: bond0 interface is not up in "
                                             "speculated time, flipping it..")
                                bond_interfaces_status = self.funcp_obj[0].is_bond_interface_up(
                                    container_name=container_name, name="bond0", flip_interface=True)
                            fun_test.test_assert_expected(
                                expected=True, actual=bond_interfaces_status,
                                message="TFTP Image boot: init-fs1600 enabled: Bond Interface is Up & Running")
                        # Configure dataplane ip as database is cleaned up
                        # Getting all the DUTs of the setup
                        nodes = self.sc_api.get_dpu_ids()
                        fun_test.test_assert(nodes,
                                             "TFTP Image boot: init-fs1600 enabled: Getting UUIDs of all DUTs "
                                             "in the setup")
                        for node_index, node in enumerate(nodes):
                            # Extracting the DUT's bond interface details
                            ip = \
                                self.fs_spec[node_index / 2].spec["bond_interface_info"][str(node_index % 2)][
                                    str(0)]["ip"]
                            ip = ip.split('/')[0]
                            subnet_mask = self.fs_spec[node_index / 2].spec["bond_interface_info"][
                                str(node_index % 2)][str(0)]["subnet_mask"]
                            route = \
                                self.fs_spec[node_index / 2].spec["bond_interface_info"][str(node_index % 2)][
                                    str(0)]["route"][0]
                            next_hop = "{}/{}".format(route["gateway"], route["network"].split("/")[1])
                            self.f1_ips.append(ip)

                            fun_test.log(
                                "TFTP Image boot: init-fs1600 enabled: Current {} node's bond0 is going to be "
                                "configured with {} IP address with {} subnet mask with next hop set to {}".
                                    format(node, ip, subnet_mask, next_hop))
                            result = self.sc_api.configure_dataplane_ip(
                                dpu_id=node, interface_name="bond0", ip=ip, subnet_mask=subnet_mask,
                                next_hop=next_hop,
                                use_dhcp=False)
                            fun_test.log("TFTP Image boot: init-fs1600 enabled: Dataplane IP configuration "
                                         "result of {}: {}".format(node, result))
                            fun_test.test_assert(result["status"],
                                                 "TFTP Image boot: init-fs1600 enabled: Configuring {} DUT "
                                                 "with Dataplane IP {}".format(node, ip))
                # Commenting manual container bringup code as all FS moved to bundle image bringup
                '''
                if not init_fs1600_service_status or (init_fs1600_service_status and not expected_containers_up):
                    fun_test.log("TFTP Image boot: Expected containers are not up, bringing up containers")
                    if init_fs1600_service_status:
                        # Disable init-fs1600 service
                        fun_test.simple_assert(disalbe_init_fs1600(self.come_obj[0]),
                                               "TFTP Image boot: init-fs1600 service is disabled")
                        init_fs1600_service_status = False

                    # Stopping containers and unloading the drivers
                    self.come_obj[0].command("sudo /opt/fungible/cclinux/cclinux_service.sh --stop")

                    # kill run_sc health_check and all containers
                    health_check_pid = self.come_obj[0].get_process_id_by_pattern("system_health_check.py")
                    if health_check_pid:
                        self.come_obj[0].kill_process(process_id=health_check_pid)
                    else:
                        fun_test.critical("TFTP Image boot: init-fs1600 disabled:"
                                          "system_health_check.py script is not running\n")

                    # Bring-up the containers
                    for index in xrange(self.num_duts):
                        # Removing existing db directories for fresh setup
                        if self.install == "fresh":
                            for directory in self.sc_db_directories:
                                if self.come_obj[index].check_file_directory_exists(path=directory):
                                    fun_test.log("TFTP Image boot: init-fs1600 disabled: Fresh Install: "
                                                 "Removing Directory {}".format(directory))
                                    self.come_obj[index].sudo_command("rm -rf {}".format(directory))
                                    fun_test.test_assert_expected(
                                        actual=self.come_obj[index].exit_status(), expected=0,
                                        message="TFTP Image boot: init-fs1600 disabled: Fresh Install: "
                                                "Directory {} is removed".format(directory))
                                else:
                                    fun_test.log("TFTP Image boot: init-fs1600 disabled: Fresh Install: "
                                                 "Directory {} does not exist skipping deletion".format(directory))
                        else:
                            fun_test.log("TFTP Image boot: init-fs1600 disabled: Fresh Install: "
                                         "Skipping run_sc restart with cleanup")
                        self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
                        self.funcp_spec[index] = self.funcp_obj[index].deploy_funcp_container(
                            update_deploy_script=self.update_deploy_script, update_workspace=self.update_workspace,
                            mode=self.funcp_mode)
                        fun_test.test_assert(
                            self.funcp_spec[index]["status"], "TFTP Image boot: init-fs1600 disabled: Starting FunCP "
                                                              "docker container in DUT {}".format(index))
                        self.funcp_spec[index]["container_names"].sort()
                        for f1_index, container_name in enumerate(self.funcp_spec[index]["container_names"]):
                            if container_name == "run_sc":
                                continue
                            bond_interfaces = self.fs_spec[index].get_bond_interfaces(f1_index=f1_index)
                            bond_name = "bond0"
                            bond_ip = bond_interfaces[0].ip
                            self.f1_ips.append(bond_ip.split('/')[0])
                            slave_interface_list = bond_interfaces[0].fpg_slaves
                            slave_interface_list = [self.fpg_int_prefix + str(i) for i in slave_interface_list]
                            self.funcp_obj[index].configure_bond_interface(
                                container_name=container_name, name=bond_name, ip=bond_ip,
                                slave_interface_list=slave_interface_list)
                            # Configuring route
                            route = self.fs_spec[index].spec["bond_interface_info"][str(f1_index)][str(0)][
                                "route"][0]
                            cmd = "sudo ip route add {} via {} dev {}".format(route["network"], route["gateway"],
                                                                              bond_name)
                            route_add_status = self.funcp_obj[index].container_info[container_name].command(cmd)
                            fun_test.test_assert_expected(
                                expected=0,
                                actual=self.funcp_obj[index].container_info[container_name].exit_status(),
                                message="TFTP Image boot: init-fs1600 disabled: Configure Static route")
                '''

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
            fun_test.shared_variables["syslog"] = self.syslog
            fun_test.shared_variables["db_log_time"] = self.db_log_time
            fun_test.shared_variables["host_info"] = self.host_info
            fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
            fun_test.shared_variables["csi_cache_miss_enabled"] = self.csi_cache_miss_enabled
            if self.csi_perf_enabled or self.csi_cache_miss_enabled:
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
            if self.csi_perf_enabled or self.csi_cache_miss_enabled:
                # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
                csi_perf_host_instance = Linux(host_ip=csi_perf_host_obj.spec["host_ip"],
                                               ssh_username=csi_perf_host_obj.spec["ssh_username"],
                                               ssh_password=csi_perf_host_obj.spec["ssh_password"])
                ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                     format(self.perf_listener_host_name, self.csi_f1_ip))

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
            fun_test.shared_variables["syslog"] = self.syslog
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
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nvme_subsystem = fun_test.shared_variables["nvme_subsystem"]

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

                # Executing NVMe disconnect from all the hosts
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
                for host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="{} - NVME Disconnect Status".format(host_name))

                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[num], ns_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume from DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)

                # Deleting all the storage controller
                for index in xrange(len(self.host_info)):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting Storage Controller {}".
                                         format(self.ctrlr_uuid[index]))
                self.storage_controller.disconnect()
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True


class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        self.sc_lock = Lock()

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "warmup_bs" in job_inputs:
            self.warm_up_fio_cmd_args["bs"] = job_inputs["warmup_bs"]
        if "warmup_io_depth" in job_inputs:
            self.warm_up_fio_cmd_args["iodepth"] = job_inputs["warmup_io_depth"]
        if "warmup_size" in job_inputs:
            self.warm_up_fio_cmd_args["io_size"] = job_inputs["warmup_size"]
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            if not isinstance(self.csi_perf_iodepth, list):
                self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False

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
            self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]
            if self.csi_perf_enabled or self.csi_cache_miss_enabled:
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

            # Attaching/Exporting all the EC/LS volumes to the external server
            self.ctrlr_uuid = []
            for index, host_name in enumerate(self.host_info):
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_id=index,
                                                                           ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.attach_transport,
                                                                           remote_ip=self.host_info[host_name]["ip"][0],
                                                                           subsys_nqn=self.nvme_subsystem,
                                                                           host_nqn=self.host_info[host_name]["ip"][0],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Create Storage Controller for {} with controller uuid {} on DUT".
                                     format(self.attach_transport, self.ctrlr_uuid[-1]))

            for num in xrange(self.ec_info["num_volumes"]):
                curr_ctrlr_index = num % self.num_hosts
                curr_host_name = self.host_info.keys()[curr_ctrlr_index]
                if "num_volumes" not in self.host_info[curr_host_name]:
                    self.host_info[curr_host_name]["num_volumes"] = 0
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[curr_ctrlr_index], ns_id=num + 1,
                    vol_uuid=self.ec_info["attach_uuid"][num], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))
                self.host_info[curr_host_name]["num_volumes"] += 1

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
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
                                                                        tcpdump_filename="/tmp/nvme_connect.pcap",
                                                                        snaplen=1500)
                if pcap_pid[host_name]:
                    fun_test.log("Started packet capture in {}".format(host_name))
                    pcap_started[host_name] = True
                    pcap_stopped[host_name] = False
                else:
                    fun_test.critical("Unable to start packet capture in {}".format(host_name))

            fun_test.shared_variables["fio"] = {}
            for host_name in self.host_info:
                fun_test.shared_variables["ec"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]
                if not fun_test.shared_variables["ec"]["nvme_connect"]:
                    # Checking nvme-connect status
                    if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                            self.testbed_config["workarounds"]["enable_funcp"]:
                        if not hasattr(self, "nvme_io_queues") or (
                                hasattr(self, "nvme_io_queues") and self.nvme_io_queues == 0):
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.attach_transport,
                                hostnqn=self.host_info[host_name]["ip"][0])
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.attach_transport,
                                nvme_io_queues=self.nvme_io_queues,
                                hostnqn=self.host_info[host_name]["ip"][0])
                    else:
                        if not hasattr(self, "nvme_io_queues") or (
                                hasattr(self, "nvme_io_queues") and self.nvme_io_queues == 0):
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.attach_transport)
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.attach_transport,
                                nvme_io_queues=self.nvme_io_queues)

                    if pcap_started[host_name]:
                        host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                        pcap_stopped[host_name] = True

                    fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

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

            # Setting the required syslog level
            if self.syslog != "default":
                command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog],
                                                              legacy=False, command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Setting syslog level to {}".format(self.syslog))

                command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

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
            fun_test.debug("vol_details is: {}".format(self.vol_details))
            fun_test.shared_variables["vol_details"] = self.vol_details

        # Executing the FIO command to fill the volume to it's capacity
        if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
            server_written_total_bytes = 0
            total_bytes_pushed_to_disk = 0
            try:
                self.sc_lock.acquire()
                initial_vol_stats = self.storage_controller.peek(
                    props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                self.sc_lock.release()
                fun_test.test_assert(initial_vol_stats["status"], "Volume stats collected before warmup")
                fun_test.debug("Volume stats before warmup: {}".format(initial_vol_stats))
            except Exception as ex:
                fun_test.critical(str(ex))

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
                    server_written_total_bytes += fun_test.shared_variables["fio"][index]["write"]["io_bytes"]
            else:
                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                      cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                      **self.warm_up_fio_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "Volume warmup on host {}".format(host_name))
                    server_written_total_bytes += fio_output["write"]["io_bytes"]

            fun_test.sleep("before actual test", self.iter_interval)
            fun_test.shared_variables["ec"]["warmup_io_completed"] = True

            try:
                self.sc_lock.acquire()
                final_vol_stats = self.storage_controller.peek(
                    props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                self.sc_lock.release()
                fun_test.test_assert(final_vol_stats["status"], "Volume stats collected after warmup")
                fun_test.debug("Volume stats after warmup: {}".format(final_vol_stats))
            except Exception as ex:
                fun_test.critical(str(ex))

            if initial_vol_stats["status"] and final_vol_stats["status"]:
                diff_vol_stats = vol_stats_diff(initial_vol_stats=initial_vol_stats["data"],
                                                final_vol_stats=final_vol_stats["data"], vol_details=self.vol_details)
                if diff_vol_stats["status"]:
                    total_bytes_pushed_to_disk = diff_vol_stats["total_diff"]["VOL_TYPE_BLK_LSV"]["write_bytes"]
                    compress_ratio = round(server_written_total_bytes / float(total_bytes_pushed_to_disk), 2)

                    headers = ["Total bytes written by server", "Total bytes pushed to disk after compression",
                               "Compression Ratio"]
                    data = [server_written_total_bytes, total_bytes_pushed_to_disk, compress_ratio]
                    table_data = {"headers": headers, "rows": [data]}
                    fun_test.add_table(panel_header="Compression Details", table_name="Compression ratio during warmup",
                                       table_data=table_data)
                else:
                    fun_test.critical("Unable to compute difference between the final & initial volumes stats during "
                                      "warmup...So skipping compression ratio calculation")

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Num Hosts", "Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name", "Write Amplification Vol Stats",
                              "Read Amplification Vol Stats", "Aggregated Amplification Vol Stats",
                              "Write Amplification App Stats", "Read Amplification App Stats",
                              "Aggregated Amplification App Stats", "Write Amplification rcnvme Stats",
                              "Read Amplification rcnvme Stats", "Aggregated Amplification rcnvme Stats"]
        table_data_cols = ["num_hosts", "block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw",
                           "readbw", "writeclatency", "writelatency90", "writelatency95", "writelatency99",
                           "writelatency9999", "readclatency", "readlatency90", "readlatency95", "readlatency99",
                           "readlatency9999", "fio_job_name", "write_amp_vol_stats", "read_amp_vol_stats",
                           "aggr_amp_vol_stats", "write_amp_app_stats", "read_amp_app_stats", "aggr_amp_app_stats",
                           "write_amp_rcnvme_stats", "read_amp_rcnvme_stats", "aggr_amp_rcnvme_stats"]
        table_data_rows = []

        ssd_util_headers = ["IO Depth"]
        for i in range(12):
            ssd_util_headers.append("SSD{} IOPS".format(i))
        ssd_util_data_rows = []

        self.ec_info = fun_test.shared_variables["ec_info"]
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
        if "rwmixread" in job_inputs and "rwmixread" in self.fio_cmd_args["multiple_jobs"]:
            self.rwmixread = job_inputs["rwmixread"]
            self.fio_cmd_args["multiple_jobs"] = re.sub(r"--rwmixread=\d+ ", "--rwmixread={} ".format(self.rwmixread),
                                                        self.fio_cmd_args["multiple_jobs"])
            fun_test.log("FIO param --rwmixread is overridden by user to: --rwmixread={}".format(self.rwmixread))

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}
        initial_stats = {}
        final_stats = {}
        resultant_stats = {}
        aggregate_resultant_stats = {}
        initial_vol_stat = {}
        final_vol_stat = {}
        initial_rcnvme_stat = {}
        final_rcnvme_stat = {}

        start_stats = True

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}
            fio_job_args = ""
            fio_cmd_args = {}
            mpstat_pid = {}
            mpstat_artifact_file = {}
            initial_stats[iodepth] = {}
            final_stats[iodepth] = {}
            resultant_stats[iodepth] = {}
            aggregate_resultant_stats[iodepth] = {}
            initial_vol_stat[iodepth] = {}
            final_vol_stat[iodepth] = {}
            initial_rcnvme_stat[iodepth] = {}
            final_rcnvme_stat[iodepth] = {}

            test_thread_id = {}
            host_clone = {}

            row_data_dict = {}
            ssd_util_row_data = {}
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
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--bs=(\w+)", self.fio_cmd_args["multiple_jobs"])
                if match:
                    fio_block_size = match.group(1)
                else:
                    match = re.search("--bssplit=((\w+/\w+:*)+)", self.fio_cmd_args["multiple_jobs"])
                    if match:
                        fio_block_size = "Mixed"

            if "rw" in self.fio_cmd_args:
                row_data_dict["mode"] = self.fio_cmd_args["rw"]
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--rw=(\w+)", self.fio_cmd_args["multiple_jobs"])
                if match:
                    row_data_dict["mode"] = match.group(1)
            else:
                row_data_dict["mode"] = "Combined"

            row_data_dict["block_size"] = fio_block_size

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
                self.stats_obj = CollectStats(storage_controller=self.storage_controller, sc_lock=self.sc_lock)
                self.stats_obj.start(file_suffix, self.stats_collect_details)
                fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                             "them:\n{}".format(iodepth, self.stats_collect_details))
            else:
                fun_test.critical("Not starting the vp_utils and resource_bam stats collection because of lack of "
                                  "interval and count details")

            if self.cal_amplification:
                try:
                    self.sc_lock.acquire()
                    initial_vol_stat[iodepth] = self.storage_controller.peek(
                        props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                    self.sc_lock.release()
                    fun_test.test_assert(initial_vol_stat[iodepth]["status"], "Volume stats collected before the test")
                    fun_test.debug("Initial vol stats in script: {}".format(initial_vol_stat[iodepth]))

                    self.sc_lock.acquire()
                    initial_rcnvme_stat[iodepth] = self.storage_controller.peek(
                        props_tree="storage/devices/nvme/ssds", legacy=False, chunk=8192,
                        command_duration=self.command_timeout)
                    self.sc_lock.release()
                    fun_test.test_assert(initial_rcnvme_stat[iodepth]["status"],
                                         "rcnvme stats collected before the test")
                    fun_test.debug("Initial rcnvme stats in script: {}".format(initial_rcnvme_stat[iodepth]))
                except Exception as ex:
                    fun_test.critical(str(ex))

            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
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
                ssd_util_row_data["IO Depth"] = row_data_dict["iodepth"]

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
                if self.ec_info["num_volumes"] != 1:
                    fio_job_name = "{}_iodepth_{}_vol_{}".format(self.fio_job_name, row_data_dict["iodepth"],
                                                                 self.ec_info["num_volumes"])
                    if self.ec_info.get("compress", False):
                        fio_job_name = "{}_{}pctcomp_iodepth_{}_vol_{}". \
                            format(self.fio_job_name, self.warm_up_fio_cmd_args["buffer_compress_percentage"],
                                   row_data_dict["iodepth"], self.ec_info["num_volumes"])

                    if self.ec_info.get("encrypt", False):
                        fio_job_name = "{}_encryption_keysize_{}_iodepth_{}_vol_{}". \
                            format(self.fio_job_name,self.ec_info["key_size"],row_data_dict["iodepth"], self.ec_info["num_volumes"])
                else:
                    fio_job_name = "{}_{}".format(self.fio_job_name, row_data_dict["iodepth"])

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
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

            # Starting csi perf stats collection if it's set
            if self.csi_perf_enabled or self.csi_cache_miss_enabled:
                if row_data_dict["iodepth"] in self.csi_perf_iodepth:
                    try:
                        fun_test.sleep("for IO to be fully active", 60)
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
                        self.sc_lock.acquire()
                        final_vol_stat[iodepth] = self.storage_controller.peek(
                            props_tree="storage/volumes", legacy=False, chunk=8192,
                            command_duration=self.command_timeout)
                        self.sc_lock.release()
                        fun_test.test_assert(final_vol_stat[iodepth]["status"], "Volume stats collected after the test")
                        fun_test.debug("Final vol stats in script: {}".format(final_vol_stat[iodepth]))

                        self.sc_lock.acquire()
                        final_rcnvme_stat[iodepth] = self.storage_controller.peek(
                            props_tree="storage/devices/nvme/ssds", legacy=False, chunk=8192,
                            command_duration=self.command_timeout)
                        self.sc_lock.release()
                        fun_test.test_assert(final_rcnvme_stat[iodepth]["status"],
                                             "rcnvme stats collected after the test")
                        fun_test.debug("Final rcnvme stats in script: {}".format(final_rcnvme_stat[iodepth]))
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
                    # Converting the runtime from milliseconds to seconds and taking the average out of it
                    if field == "runtime":
                        aggr_fio_output[iodepth][op][field] = int(round(value / 1000) / self.num_hosts)
                    row_data_dict[op + field] = aggr_fio_output[iodepth][op][field]

            fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            if not aggr_fio_output[iodepth]:
                fio_result[iodepth] = False
                fun_test.critical("No output from FIO test, hence moving to the next variation")
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
                        fun_test.debug("\ninitial_vol_stat[{}] is: {}\n".
                                     format(iodepth, initial_vol_stat[iodepth]["data"]))
                        fun_test.debug("\nfinal_vol_stat[{}] is: {}\n".format(iodepth, final_vol_stat[iodepth]["data"]))
                        fun_test.debug("\nvol_details: {}\n".format(self.vol_details))
                        curr_stats_diff = vol_stats_diff(initial_vol_stats=initial_vol_stat[iodepth]["data"],
                                                         final_vol_stats=final_vol_stat[iodepth]["data"],
                                                         vol_details=self.vol_details)
                        fun_test.simple_assert(curr_stats_diff["status"], "Volume stats diff to measure amplification")
                        fun_test.debug("\nVolume stats diff: {}".format(curr_stats_diff))

                        pbw = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LOCAL_THIN"]["write_bytes"]
                        lbw = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LSV"]["write_bytes"]
                        lbw_app = aggr_fio_output[iodepth]['write']["io_bytes"]
                        pbr = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LOCAL_THIN"]["read_bytes"]
                        lbr = curr_stats_diff["total_diff"]["VOL_TYPE_BLK_LSV"]["read_bytes"]
                        lbr_app = aggr_fio_output[iodepth]['read']["io_bytes"]

                        fun_test.debug("Iodepth: {}\nPhysical Bytes Written from volume stats: {}"
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
                        fun_test.debug("\nRCNVMe stats diff: {}".format(rcnvme_diff_stats))

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


class RandReadWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1.1: 8k data block random read/write IOPS performance of Multiple"
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


class RandRead8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.11.1.2: 8k data block random read IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read IOPS
        """)

    def setup(self):
        super(RandRead8kBlocks, self).setup()

    def run(self):
        super(RandRead8kBlocks, self).run()

    def cleanup(self):
        super(RandRead8kBlocks, self).cleanup()


class RandWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Inspur TC 8.11.1.3: 8k data block random write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random write IOPS
        """)

    def setup(self):
        super(RandWrite8kBlocks, self).setup()

    def run(self):
        super(RandWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandWrite8kBlocks, self).cleanup()


class SequentialReadWrite1024kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
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
        self.set_test_details(id=5,
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
        self.set_test_details(id=6,
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
        self.set_test_details(id=7,
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
    ecscript.add_test_case(RandRead8kBlocks())
    ecscript.add_test_case(MixedRandReadWriteIOPS())
    ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    ecscript.add_test_case(RandWrite8kBlocks())
    #ecscript.add_test_case(OLTPModelReadWriteIOPS())
    #ecscript.add_test_case(OLAPModelReadWriteIOPS())
    ecscript.run()
