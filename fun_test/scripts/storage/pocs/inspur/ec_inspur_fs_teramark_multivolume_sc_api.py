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
            fun_test.shared_variables["sc_api_obj"] = self.sc_api
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
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.fs = fun_test.shared_variables["fs_obj"]
        self.host_info = fun_test.shared_variables["host_info"]
        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][self.f1_in_use]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = len(self.host_info)
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]

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

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            sc = fun_test.shared_variables["sc_api_obj"]

            try:
                pool_uuid = sc.execute_api("GET", "storage/pools")
                pool_uuid = pool_uuid.json()
                self.pool_uuid = pool_uuid["data"].keys()[0]

            except Exception as ex:
                fun_test.critical(str(ex))
            volume_uuid_list = []
            self.nqn_list = []
            self.host_nqn_list = []
            host_ips = []
            count = 0
            for index, host_name in enumerate(self.host_info):
                host_ips.append(self.host_info[host_name]["ip"][index])

            for num in xrange(self.ec_info["num_volumes"]):

                response = sc.create_volume(self.pool_uuid, self.ec_info["volume_name"], self.ec_info["capacity"],
                                            self.ec_info["stripe_count"], self.ec_info["volume_types"]["ec"],
                                            self.ec_info["encrypt"], self.ec_info["allow_expansion"],
                                            self.ec_info["data_protection"], self.ec_info["compression_effort"])
                fun_test.log("Create EC volume API response: {}".format(response))

                fun_test.test_assert(response["status"], "Create EC Volume {}".
                                     format(count + 1))
                volume_uuid_list.append(response["data"]["uuid"])
                attach_volume = sc.volume_attach_remote(vol_uuid=response["data"]["uuid"],
                                                        transport=self.attach_transport.upper(),
                                                        remote_ip=host_ips[num])
                host_nqn = attach_volume["data"]["host_nqn"]
                subsys_nqn = attach_volume["data"]["subsys_nqn"] if "subsys_nqn" in attach_volume["data"] else \
                    attach_volume["data"].get("nqn")
                fun_test.simple_assert(subsys_nqn, "Extracted the Subsys NQN to which volume {} got attached".
                                       format(response["data"]["uuid"]))
                self.nqn_list.append(subsys_nqn)
                self.host_nqn_list.append(host_nqn)
                fun_test.log("Attach volume API response: {}".format(attach_volume))
                fun_test.test_assert(attach_volume["status"], "Attaching EC volume {} to the host {}".
                                     format(response["data"]["uuid"], host_ips[num]))
                count += 1
            # Starting packet capture in all the hosts
            fun_test.shared_variables["volume_uuid_list"] = volume_uuid_list
            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                host_ip = self.host_info[host_name]["ip"][index]
                nqn = self.nqn_list[index]

                host_nqn_workaround = True

                host_nqn_val = None
                if host_nqn_workaround:
                    host_nqn_val = self.nqn_list[index].split(":")[0] + ":" + self.host_nqn_list[index]
                else:
                    host_nqn_val = self.host_nqn_list[index]

                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")
                if "dead" in irq_bal_stat:
                    fun_test.log("IRQ balance stopped on {}".format(host_name))
                else:
                    fun_test.log("IRQ balance not stopped on {}".format(host_name))
                    install_status = host_handle.install_package("tuned")
                    fun_test.test_assert(install_status, "tuned installed successfully")

                    host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

                command_result = host_handle.command("lsmod | grep -w nvme")
                if "nvme" in command_result:
                    fun_test.log("nvme driver is loaded")
                else:
                    fun_test.log("Loading nvme")
                    host_handle.modprobe("nvme")
                    host_handle.modprobe("nvme_core")
                command_result = host_handle.lsmod("nvme_tcp")
                if "nvme_tcp" in command_result:
                    fun_test.log("nvme_tcp driver is loaded")
                else:
                    fun_test.log("Loading nvme_tcp")
                    host_handle.modprobe("nvme_tcp")
                    host_handle.modprobe("nvme_fabrics")
                nvme_connect_cmd_res = None

                host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    nvme_connect_cmd_res = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.attach_transport),
                                                                                  self.test_network["f1_loopback_ip"],
                                                                                  self.transport_port, nqn,
                                                                                  self.nvme_io_queues, host_nqn_val))
                    fun_test.log(nvme_connect_cmd_res)
                else:
                    nvme_connect_cmd_res = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.attach_transport),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            self.transport_port, nqn, host_nqn_val))
                    fun_test.log(nvme_connect_cmd_res)
                fun_test.test_assert(expression="error" not in nvme_connect_cmd_res,
                                     message="nvme connect command succesful")
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                host_handle.sudo_command("dmesg")

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")
                fun_test.log("lsblk Output: \n{}".format(lsblk_output))

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

                self.host_info[host_name]["nvme_block_device_list"].sort()
                self.host_info[host_name]["fio_filename"] = ":".join(
                    self.host_info[host_name]["nvme_block_device_list"])
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

        # Executing the FIO command to fill the volume to it's capacity
        if self.warm_up_traffic:
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

            thread_id = {}
            end_host_thread = {}
            if self.warm_up_traffic:
                # self.nvme_block_device_str = ':'.join(self.nvme_block_device)
                # fun_test.shared_variables["nvme_block_device_str"] = self.nvme_block_device_str
                fio_output = {}
                for index, host_name in enumerate(self.host_info):
                    fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                                 "provided")
                    warm_up_fio_cmd_args = {}
                    jobs = ""
                    fio_output[index] = {}
                    end_host_thread[index] = self.host_info[host_name]["handle"].clone()
                    wait_time = self.num_hosts - index
                    if "multiple_jobs" in self.warm_up_fio_cmd_args:
                        # Adding the allowed CPUs into the fio warmup command
                        # self.warm_up_fio_cmd_args["multiple_jobs"] += "  --cpus_allowed={}".\
                        #    format(self.host_info[host_name]["host_numa_cpus"])
                        fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                        for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                            jobs += " --name=pre-cond-job-{} --filename={}".format(id + 1, device)
                        warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + str(
                            fio_cpus_allowed_args) + str(jobs)
                        warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]
                        # fio_output = self.host_handles[key].pcie_fio(filename="nofile", timeout=self.warm_up_fio_cmd_args["timeout"],
                        #                                    **warm_up_fio_cmd_args)
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **warm_up_fio_cmd_args)
                    else:
                        # Adding the allowed CPUs into the fio warmup command
                        self.warm_up_fio_cmd_args["cpus_allowed"] = self.host_info[host_name]["host_numa_cpus"]
                        # fio_output = self.host_handles[key].pcie_fio(filename=self.nvme_block_device_str, **self.warm_up_fio_cmd_args)
                        filename = self.host_info[host_name]["fio_filename"]
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename=filename,
                                                                         **self.warm_up_fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for index, host_name in enumerate(self.host_info):
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=thread_id[index])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][index])
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                             format(host_name))
                        fio_output[index] = {}
                        fio_output[index] = fun_test.shared_variables["fio"][index]

                except Exception as ex:
                    fun_test.log("Fio warmup failed")
                    fun_test.critical(str(ex))

                fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]
        # self.test_mode = testcase[12:]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
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

        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[self.ec_info["volume_types"]["ec"]] = fun_test.shared_variables["volume_uuid_list"]
        vol_details.append(vol_group)

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_jobs_iodepth = job_inputs["io_depth"]
            fun_test.log("Overrided fio_jobs_iodepth: {}".format(self.fio_jobs_iodepth))

        if not isinstance(self.fio_jobs_iodepth, list):
            self.fio_jobs_iodepth = [self.fio_jobs_iodepth]

        for combo in self.fio_jobs_iodepth:
            thread_id = {}
            end_host_thread = {}
            iostat_thread = {}
            final_fio_output = {}
            tmp = combo.split(',')
            fio_numjobs = tmp[0].strip('() ')
            fio_iodepth = tmp[1].strip('() ')

            if "RandReadWrite" in testcase:
                mode_action = "RandReadWrite"
            elif "RandWrite" in testcase:
                mode_action = "RandWrite"
            else:
                mode_action = "RandRead"

            file_suffix = "{}_iodepth_{}.txt".format(mode_action, (int(fio_iodepth) * int(fio_numjobs)))
            for index, stat_detail in enumerate(self.stats_collect_details):
                func = stat_detail.keys()[0]
                self.stats_collect_details[index][func]["count"] = int(
                    self.fio_runtime / self.stats_collect_details[index][func]["interval"])
                if func == "vol_stats":
                    self.stats_collect_details[index][func]["vol_details"] = vol_details
            fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))
            self.storage_controller.verbose = False
            stats_obj = CollectStats(self.storage_controller)
            stats_obj.start(file_suffix, self.stats_collect_details)
            fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))

            for i, host_name in enumerate(self.host_info):
                fio_result[combo] = {}
                fio_output[combo] = {}
                final_fio_output[combo] = {}
                internal_result[combo] = {}
                row_data_dict = {}
                end_host_thread[i] = self.host_info[host_name]["handle"].clone()

                for mode in self.fio_modes:
                    fio_block_size = self.fio_bs
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True

                    row_data_dict["mode"] = mode
                    row_data_dict["block_size"] = fio_block_size
                    row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                    row_data_dict["num_jobs"] = fio_numjobs
                    file_size_in_gb = self.ec_info["capacity"] / 1073741824
                    row_data_dict["size"] = str(file_size_in_gb) + "GB"

                    fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                                 format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                    starting_core = int(self.host_info[host_name]["host_numa_cpus"].split(',')[0].split('-')[0]) + 1
                    if int(fio_numjobs) == 1:
                        cpus_allowed = str(starting_core)
                    elif int(fio_numjobs) == 4:
                        cpus_allowed = "{}-4".format(starting_core)
                    elif int(fio_numjobs) > 4:
                        cpus_allowed = "{}-{}".format(starting_core, self.host_info[host_name]["host_numa_cpus"][2:])
                    else:
                        cpus_allowed = str(starting_core)
                    """
                    # Flush cache before read test
                    self.end_host.sudo_command("sync")
                    self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")
                    """

                    fun_test.log("Running FIO...")
                    # fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_vol_" + str(self.blt_count)
                    fio_job_name = "fio_tcp_{}_blt_{}_{}_vol".format(mode, fio_numjobs, fio_iodepth)
                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    fio_output[combo][mode] = {}
                    final_fio_output[combo][mode] = {}
                    """
                    if hasattr(self, "test_blt_count") and self.test_blt_count == 1:
                        fio_filename = fun_test.shared_variables["nvme_block_device_list"][0]
                    else:
                        fio_filename = fun_test.shared_variables["nvme_block_device_str"]
                    """
                    # fio_filename = str(fun_test.shared_variables["vol_list"][i]["vol_name"])
                    wait_time = self.num_hosts - i
                    """
                    fio_output[combo][mode] = self.end_host.pcie_fio(filename=fio_filename,
                                                                    numjobs=fio_numjobs,
                                                                    rw=mode,
                                                                    bs=fio_block_size,
                                                                    iodepth=fio_iodepth,
                                                                    name=fio_job_name,
                                                                    cpus_allowed=cpus_allowed,
                                                                    **self.fio_cmd_args)
                    """
                    # Deciding the FIO runtime based on the current IO depth
                    if row_data_dict["iodepth"] in self.full_run_iodepth:
                        fio_runtime = self.fio_full_run_time
                        fio_timeout = self.fio_full_run_timeout
                    else:
                        fio_runtime = self.fio_runtime
                        fio_timeout = self.fio_run_timeout
                    # Building the FIO command
                    fio_cmd_args = {}

                    runtime_global_args = " --runtime={} --cpus_allowed={} --bs={} --rw={} --numjobs={} --iodepth={}". \
                        format(fio_runtime, cpus_allowed, fio_block_size, mode, fio_numjobs, fio_iodepth)
                    jobs = ""
                    for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)

                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"] + runtime_global_args + jobs
                    fio_cmd_args["timeout"] = fio_timeout

                    thread_id[i] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser, arg1=end_host_thread[i],
                                                                 host_index=i, filename="nofile", **fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

            fun_test.sleep("Fio threads started", 10)
            # Starting csi perf stats collection if it's set
            if self.csi_perf_enabled:
                if row_data_dict["iodepth"] in self.csi_perf_iodepth:
                    try:
                        fun_test.sleep("for IO to be fully active", 120)
                        csi_perf_obj = CsiPerfTemplate(perf_collector_host_name=str(self.perf_listener_host_name),
                                                       listener_ip=self.perf_listener_ip, fs=self.fs[0],
                                                       listener_port=4420)  # Temp change for testing
                        csi_perf_obj.prepare(f1_index=0)
                        csi_perf_obj.start(f1_index=0, dpc_client=self.storage_controller)
                        fun_test.log("csi perf stats collection is started")
                        # dpcsh_client = self.fs.get_dpc_client(f1_index=0, auto_disconnect=True)
                        fun_test.sleep("Allowing CSI performance data to be collected", 300)
                        csi_perf_obj.stop(f1_index=0, dpc_client=self.storage_controller)
                        fun_test.log("CSI perf stats collection is done")
                    except Exception as ex:
                        fun_test.critical(str(ex))
                else:
                    fun_test.log("Skipping CSI perf collection for current iodepth {}".format(
                        (int(fio_iodepth) * int(fio_numjobs))))
            else:
                fun_test.log("CSI perf collection is not enabled, hence skipping it for current test")

            try:
                for i, host_name in enumerate(self.host_info):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "Fio {} test with IO depth {} in host {}".
                                         format(mode, int(fio_iodepth) * int(fio_numjobs), host_name))
                    fio_output[combo][mode][i] = {}
                    fio_output[combo][mode][i] = fun_test.shared_variables["fio"][i]
                final_fio_output[combo][mode] = fio_output[combo][mode][0]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output for volume {}:\n {}".format(i, fio_output[combo][mode][i]))
            finally:
                stats_obj.stop(self.stats_collect_details)
                self.storage_controller.verbose = True

            for index, value in enumerate(self.stats_collect_details):
                for func, arg in value.iteritems():
                    filename = arg.get("output_file")
                    if filename:
                        if func == "vp_utils":
                            fun_test.add_auxillary_file(description="F1 VP Utilization - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "per_vp":
                            fun_test.add_auxillary_file(description="F1 Per VP Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "resource_bam_args":
                            fun_test.add_auxillary_file(description="F1 Resource bam stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "vol_stats":
                            fun_test.add_auxillary_file(description="Volume Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "vppkts_stats":
                            fun_test.add_auxillary_file(description="VP Pkts Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "psw_stats":
                            fun_test.add_auxillary_file(description="PSW Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "fcp_stats":
                            fun_test.add_auxillary_file(description="FCP Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "wro_stats":
                            fun_test.add_auxillary_file(description="WRO Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "erp_stats":
                            fun_test.add_auxillary_file(description="ERP Stats - {} IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "etp_stats":
                            fun_test.add_auxillary_file(description="ETP Stats - {} IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "eqm_stats":
                            fun_test.add_auxillary_file(description="EQM Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "hu_stats":
                            fun_test.add_auxillary_file(description="HU Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "ddr_stats":
                            fun_test.add_auxillary_file(description="DDR Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "ca_stats":
                            fun_test.add_auxillary_file(description="CA Stats - {} IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)
                        if func == "cdu_stats":
                            fun_test.add_auxillary_file(description="CDU Stats - {} - IO depth {}".
                                                        format(mode, row_data_dict["iodepth"]), filename=filename)

            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval), self.iter_interval)
            '''
            for i in range(1, len(self.host_info)):
                fun_test.test_assert(fio_output[combo][mode][i], "Fio threaded test")
                # Boosting the fio output with the testbed performance multiplier
                multiplier = 1
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        if field == "latency":
                            fio_output[combo][mode][i][op][field] = int(round(value / multiplier))
                        final_fio_output[combo][mode][op][field] += fio_output[combo][mode][i][op][field]
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval))

            # Comparing the FIO results with the expected value for the current block size and IO depth combo
            for op, stats in self.expected_fio_result[combo][mode].items():
                for field, value in stats.items():
                    # fun_test.log("op is: {} and field is: {} ".format(op, field))
                    actual = final_fio_output[combo][mode][op][field]
                    if "latency" in str(field):
                        actual = int(round(actual / self.blt_count))
                    row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                 int((value * (1 + self.fio_pass_threshold))))

            row_data_dict["fio_job_name"] = fio_job_name
            '''
            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_rows.append(row_data_list)
            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Multi_host_TCP", test_method, *row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Multiple hosts over TCP Perf Table", table_name=self.summary,
                               table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


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
    # ecscript.add_test_case(MixedRandReadWriteIOPS())
    # ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    # ecscript.add_test_case(RandWrite8kBlocks())
    #ecscript.add_test_case(OLTPModelReadWriteIOPS())
    #ecscript.add_test_case(OLAPModelReadWriteIOPS())
    ecscript.run()
