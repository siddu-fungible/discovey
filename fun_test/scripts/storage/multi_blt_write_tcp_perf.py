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
from lib.templates.storage.storage_controller_api import *

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''


def get_iostat(host_thread, sleep_time, iostat_interval, iostat_iter):
    host_thread.sudo_command("sleep {} ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
                             format(sleep_time, iostat_interval, iostat_iter), timeout=400)
    host_thread.sudo_command("awk '/^nvme0n1/' <(cat /tmp/iostat.log) | sed 1d > /tmp/iostat_final.log")

    fun_test.shared_variables["avg_tps"] = host_thread.sudo_command(
        "awk '{ total += $2 } END { print total/NR }' /tmp/iostat_final.log")

    fun_test.shared_variables["avg_kbr"] = host_thread.sudo_command(
        "awk '{ total += $3 } END { print total/NR }' /tmp/iostat_final.log")

    host_thread.disconnect()


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
    num_volume = fun_test.shared_variables["blt_count"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volume, fio_job_name=fio_job_name,
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


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return (actual < (expected * (1 - threshold)) and ((expected - actual) > 2))
    else:
        return (actual > (expected * (1 + threshold)) and ((actual - expected) > 2))


class MultiBLTVolumePerformanceScript(FunTestScript):
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

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = "default"
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

        fun_test.test_assert(expression=self.num_duts <= self.total_available_duts,
                             message="Testbed has enough DUTs")

        self.tftp_image_path = fun_test.get_job_environment_variable("tftp_image_path")
        self.bundle_image_parameters = fun_test.get_job_environment_variable("bundle_image_parameters")
        for i in range(len(self.bootargs)):
            self.bootargs[i] += " --mgmt"

        # Deploying of DUTs
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

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
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
                fun_test.simple_assert(expression=not api_server_up_timer.is_expired(),
                                       message="Bundle Image boot: API server is up")
                fun_test.sleep("Bundle Image boot: waiting for API server to be ready", 60)
                # Check if bond interface status is Up and Running
                for f1_index, container_name in enumerate(self.funcp_spec[0]["container_names"]):
                    if container_name == "run_sc":
                        continue
                    bond_interfaces_status = self.funcp_obj[0].is_bond_interface_up(container_name=container_name,
                                                                                    name="bond0")
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
                expected_containers_up = False
                init_fs1600_service_status = False
                if init_fs1600_status(self.come_obj[0]):
                    fun_test.log("TFTP image boot: init-fs1600 service status: enabled")
                    # init-fs1600 service is enabled, checking if all the required containers are running
                    init_fs1600_service_status = True
                    expected_containers = ['F1-0', 'F1-1', 'run_sc']
                    container_chk_timer = FunTimer(max_time=(self.container_up_timeout * 2))
                    while not container_chk_timer.is_expired():
                        container_names = self.funcp_obj[0].get_container_names(
                            stop_run_sc=False, include_storage=True)['container_name_list']
                        if all(container in container_names for container in expected_containers):
                            expected_containers_up = True
                            fun_test.log("TFTP image boot: init-fs1600 enabled: Expected containers are up and running")
                            break
                        else:
                            fun_test.sleep(
                                "TFTP image boot: init-fs1600 enabled: waiting for expected containers to show up", 10)
                    if container_chk_timer.is_expired():
                        fun_test.log("TFTP image boot: init-fs1600 enabled: Expected containers are not running")
                    else:
                        # Cleaning up DB by restarting run_sc.py script with -c option
                        if "run_sc" in container_names and self.install == "fresh":
                            fun_test.log(
                                "TFTP image boot: init-fs1600 enabled: It's a fresh install. Cleaning up the database")
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
                                    fun_test.test_assert_expected(
                                        expected=True, actual=bond_interfaces_status,
                                        message="Bundle Image boot: Bond Interface is Up & Running")
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
            fun_test.shared_variables["syslog"] = self.syslog
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

            topology_helper = TopologyHelper()
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                              1: {"boot_args": self.bootargs[1]}})
            #topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]}}, disable_f1_index=1)
            self.topology = topology_helper.deploy()
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
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["enable_funcp"]:
                self.fs = self.fs_objs[0]
                self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            elif "workarounds" in self.testbed_config and "csr_replay" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["csr_replay"]:
                self.fs = fun_test.shared_variables["fs"]
                self.storage_controller = fun_test.shared_variables["storage_controller"]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]

                # Deleting the volumes
                for i in range(0, fun_test.shared_variables["blt_count"], 1):
                    cur_uuid = fun_test.shared_variables["thin_uuid"][i]
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid, ns_id=i + 1, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

                    command_result = self.storage_controller.delete_volume(uuid=cur_uuid,
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, cur_uuid))

                # Deleting the controller
                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Storage Controller Delete")

            except:
                fun_test.log("Clean-up of volumes failed.")

        fun_test.log("FS cleanup")
        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            for fs in fun_test.shared_variables["fs_objs"]:
                fs.cleanup()
        else:
            fun_test.shared_variables["fs"].cleanup()


class MultiBLTVolumePerformanceTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Numjobs and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Setting expected FIO results
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))

        if "fio_sizes" in benchmark_dict[testcase]:
            if len(self.fio_sizes) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in FIO sizes and its benchmarking results")
        elif "fio_jobs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_jobs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in numjobs and IO depth combo and its benchmarking results")

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            self.fs = fun_test.shared_variables["fs_objs"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1 = fun_test.shared_variables["f1_objs"][0][0]
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

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
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

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                                  "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.nvme_block_device = []
            self.thin_uuid_list = []
            for i in range(0, self.blt_count, 1):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_details["capacity"],
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i + 1),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i + 1, cur_uuid))
                self.nvme_block_device.append(self.nvme_device + "n" + str(i + 1))
            fun_test.shared_variables["nvme_block_device_list"] = self.nvme_block_device
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

            # Create TCP controller
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(
                ctrlr_uuid=self.ctrlr_uuid,
                transport=unicode.upper(self.transport_type),
                remote_ip=self.remote_ip,
                nqn=self.nqn,
                port=self.transport_port,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating controller for {} with uuid {} on DUT".
                                 format(self.transport_type, self.ctrlr_uuid))

            # Attach controller to all BLTs
            for i in range(0, self.blt_count, 1):
                vol_uuid = fun_test.shared_variables["thin_uuid"][i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 vol_uuid=vol_uuid,
                                                                                 ns_id=i + 1,
                                                                                 command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                 format(vol_uuid, self.ctrlr_uuid))

            self.end_host.sudo_command("iptables -F")
            self.end_host.sudo_command("ip6tables -F")
            self.end_host.sudo_command("dmesg -c > /dev/null")

            try:
                self.end_host.sudo_command("service irqbalance stop")
                fun_test.sleep("Disable irqbalance", 5)
                command_result = self.end_host.sudo_command("service irqbalance status")
                if "inactive" in command_result:
                    fun_test.log("IRQ balance disabled")
                else:
                    fun_test.critical("IRQ Balance still active")
            except:
                fun_test.log("irqbalance service not found")

            install_status = self.end_host.install_package("tuned")
            fun_test.test_assert(install_status, "tuned installed successfully")

            active_profile = self.end_host.sudo_command("tuned-adm active")
            if "network-throughput" not in active_profile:
                self.end_host.sudo_command("tuned-adm profile network-throughput")

            command_result = self.end_host.command("lsmod | grep -w nvme")
            if "nvme" in command_result:
                fun_test.log("nvme driver is loaded")
            else:
                fun_test.log("Loading nvme")
                self.end_host.modprobe("nvme")
                self.end_host.modprobe("nvme_core")
            command_result = self.end_host.lsmod("nvme_tcp")
            if "nvme_tcp" in command_result:
                fun_test.log("nvme_tcp driver is loaded")
            else:
                fun_test.log("Loading nvme_tcp")
                self.end_host.modprobe("nvme_tcp")
                self.end_host.modprobe("nvme_fabrics")

            # Setting the required syslog level
            if self.syslog != "default":
                command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
                fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

                command_result = self.storage_controller.peek("params/syslog/level")
                fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

            fun_test.sleep("x86 Config done", seconds=10)
            if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".
                        format(unicode.lower(self.transport_type),
                               self.test_network["f1_loopback_ip"],
                               str(self.transport_port),
                               self.nqn,
                               self.nvme_io_queues,
                               self.remote_ip))
                fun_test.log(command_result)
            else:
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".
                        format(unicode.lower(self.transport_type),
                               self.test_network["f1_loopback_ip"],
                               str(self.transport_port),
                               self.nqn,
                               self.remote_ip))
                fun_test.log(command_result)

            # Checking that the above created BLT volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            for i in range(0, self.blt_count, 1):
                self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(i + 1)
                lsblk_output = self.end_host.lsblk()
                fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                                message="{} device type check".format(self.volume_name))

            fun_test.shared_variables["blt"]["setup_created"] = True

            # Pre-conditioning the volume (one time task)
            self.nvme_block_device_str = ':'.join(self.nvme_block_device)
            fun_test.shared_variables["nvme_block_device_str"] = self.nvme_block_device_str
            if self.warm_up_traffic:
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                warm_up_fio_cmd_args = {}
                jobs = ""
                if "multiple_jobs" in self.warm_up_fio_cmd_args:
                    for i in range(0, len(self.nvme_block_device)):
                         jobs += " --name=pre-cond-job-{} --filename={}".format(i + 1, self.nvme_block_device[i])
                    warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + str(jobs)
                    fio_output = self.end_host.pcie_fio(filename="nofile", timeout=self.warm_up_fio_cmd_args["timeout"],
                                                        **warm_up_fio_cmd_args)
                else:
                    fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device_str, **self.warm_up_fio_cmd_args)
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.test_mode = testcase[:]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_status = {}
        final_volume_status = {}
        diff_volume_stats = {}
        initial_stats = {}
        final_stats = {}
        diff_stats = {}

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
        vol_group[self.blt_details["type"]] = fun_test.shared_variables["thin_uuid"]
        vol_details.append(vol_group)

        for combo in self.fio_jobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            initial_stats[combo] = {}
            final_stats[combo] = {}
            diff_stats[combo] = {}

            tmp = combo.split(',')
            fio_numjobs = tmp[0].strip('() ')
            fio_iodepth = tmp[1].strip('() ')

            # Starting stats collection
            file_suffix = "{}_iodepth_{}.txt".format(self.test_mode, (int(fio_iodepth) * int(fio_numjobs)))
            for index, stat_detail in enumerate(self.stats_collect_details):
                func = stat_detail.keys()[0]
                self.stats_collect_details[index][func]["count"] = int(
                    self.fio_cmd_args["runtime"] / self.stats_collect_details[index][func]["interval"])
                if func == "vol_stats":
                    self.stats_collect_details[index][func]["vol_details"] = vol_details
            fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))
            self.storage_controller.verbose = False
            stats_obj = CollectStats(self.storage_controller)
            stats_obj.start(file_suffix, self.stats_collect_details)
            fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))

            for mode in self.fio_modes:
                fio_block_size = self.fio_bs
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                row_data_dict["num_jobs"] = fio_numjobs
                file_size_in_gb = self.blt_details["capacity"] / 1073741824
                row_data_dict["size"] = str(file_size_in_gb) + "GB"

                fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                             format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                if int(fio_numjobs) == 1:
                    cpus_allowed = "1"
                elif int(fio_numjobs) == 4:
                    cpus_allowed = "1-4"
                elif int(fio_numjobs) > 4:
                    cpus_allowed = "1-19,40-59"

                # Flush cache before read test
                self.end_host.sudo_command("sync")
                self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")

                """
                # Check EQM stats before test
                self.eqm_stats_before = {}
                self.eqm_stats_before = self.storage_controller.peek(props_tree="stats/eqm")

                # Get iostat results
                self.iostat_host_thread = self.end_host.clone()
                iostat_thread = fun_test.execute_thread_after(time_in_seconds=1,
                                                              func=get_iostat,
                                                              host_thread=self.iostat_host_thread,
                                                              sleep_time=self.fio_cmd_args["runtime"] / 4,
                                                              iostat_interval=self.iostat_details["interval"],
                                                              iostat_iter=(self.fio_cmd_args["runtime"] / 4) + 1)
                """

                fun_test.log("Running FIO...")
                fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                if hasattr(self, "test_blt_count") and self.test_blt_count == 1:
                    fio_filename = fun_test.shared_variables["nvme_block_device_list"][0]
                else:
                    fio_filename = fun_test.shared_variables["nvme_block_device_str"]
                try:
                    fio_output[combo][mode] = self.end_host.pcie_fio(filename=fio_filename,
                                                                     numjobs=fio_numjobs,
                                                                     rw=mode,
                                                                     bs=fio_block_size,
                                                                     iodepth=fio_iodepth,
                                                                     name=fio_job_name,
                                                                     cpus_allowed=cpus_allowed,
                                                                     **self.fio_cmd_args)
                except Exception as ex:
                    fun_test.critical(str(ex))
                    fun_test.log("FIO Command Output:\n {}".format(fio_output[combo][mode]))
                finally:
                    # Stopping stats collection
                    stats_obj.stop(self.stats_collect_details)
                    self.storage_controller.verbose = True

                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.test_assert(fio_output[combo][mode], "Fio {} test for numjobs {} & iodepth {}".
                                     format(mode, fio_numjobs, fio_iodepth))

                """
                self.eqm_stats_after = {}
                self.eqm_stats_after = self.storage_controller.peek(props_tree="stats/eqm")
                
                for field, value in self.eqm_stats_before["data"].items():
                    current_value = self.eqm_stats_after["data"][field]
                    if (value != current_value) and (field != "incoming BN msg valid"):
                        # fun_test.test_assert_expected(value, current_value, "EQM {} stat mismatch".format(field))
                        stat_delta = current_value - value
                        fun_test.critical("There is a mismatch in {} stat, delta {}".
                                          format(field, stat_delta))
                """

                """
                # Boosting the fio output with the testbed performance multiplier
                multiplier = tb_config["dut_info"][0]["perf_multiplier"]
                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value * multiplier))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value * multiplier / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value / multiplier))
                fun_test.log("FIO Command Output after multiplication:")
                """
                fun_test.log(fio_output[combo][mode])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = actual
                        fun_test.log("raw_data[op + field] is: {}".format(row_data_dict[op + field]))

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("Multi_vol_TCP", test_method, *row_data_list)

                # Creating artifacts for all collected stats
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

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Single/Multiple Volume(s) over TCP Perf Table", table_name=self.summary,
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


class SingleBLTFioWrite(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write performance for 1 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Sequential Write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')


class SingleBLTFioRandWrite(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Write performance for 1 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random Write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')


class MultiBLTFioWrite12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Sequential Read performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size of 4K",
                              steps='''
        1. Create 12 BLT volumes on FS attached with 12 SSD
        2. Create a storage controller for TCP and attach above volume to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Sequential Write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')


class MultiBLTFioRandWrite12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Random Write performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size of 4K",
                              steps='''
        1. Create 12 BLT volumes on FS attached with 12 SSD
        2. Create a storage controller for TCP and attach above volume to this controller
        3. Connect to this volume from remote host
        4. Run the FIO Random Write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":

    bltscript = MultiBLTVolumePerformanceScript()
    bltscript.add_test_case(SingleBLTFioRandWrite())
    bltscript.add_test_case(MultiBLTFioRandWrite12())
    bltscript.run()
