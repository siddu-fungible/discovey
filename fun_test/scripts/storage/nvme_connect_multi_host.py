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
from lib.templates.storage.storage_controller_api import *

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

        self.tftp_image_path = fun_test.get_job_environment_variable("tftp_image_path")
        self.bundle_image_parameters = fun_test.get_job_environment_variable("bundle_image_parameters")
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
            # Retrieving host ip
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
                    self.come_obj[0].command("sudo ./{} -c restart".format(self.run_sc_script))
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
                            self.come_obj[0].command("sudo ./{} -c restart".format(self.run_sc_script))
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
        fun_test.shared_variables["syslog_level"] = self.syslog
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

        # Ensuring connectivity from Host to F1's
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            for index, ip in enumerate(self.f1_ips):
                ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(host_name, self.funcp_spec[0]["container_names"][index], ip))

        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["ip_cfg"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        come_reboot = False
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
        fun_test.log("FS cleanup")
        for fs in fun_test.shared_variables["fs_objs"]:
            fs.cleanup()


class MultiNvmeConnect(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect no of hosts with one blt each and issue nvme connect disconnect "
                                      "continuously until hit the issue",
                              steps='''
        1. Create 1 BLT volumes fro each host
        2. Create a storage controller for TCP and attach above volumes to this controller. Strt TCPDUMP
        3. Do NVME connect from each host see if you are hitting swos-5844.
        4. If pass disconnect and do for next iteration. if fails stop TCPDUMP and collect the logs
        ''')

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

        if not hasattr(self, "blt_count"):
            self.blt_count = 12
        if not hasattr(self, "no_of_nvme_connect"):
            self.no_of_nvme_connect = 10

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog_level"]
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "no_of_nvme_connect" in job_inputs:
            self.no_of_nvme_connect = job_inputs["no_of_nvme_connect"]

        fun_test.shared_variables["blt_details"] = self.blt_details

        # Enabling counters
        """
        command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                              command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
        """

        # Configuring controller IP
        if not fun_test.shared_variables["blt"]["ip_cfg"]:
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")
            fun_test.shared_variables["blt"]["ip_cfg"] = True

        # Create BLT's
        self.vol_list = []
        self.thin_uuid_list = []

        for i in range(self.blt_count):
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
            self.vol_list.append(vol_details)

        fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

        # Create TCP controllers (1 for each SSD and Host)
        self.ctrlr_uuid = []
        for i in range(self.blt_count):
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
            self.vol_list[i]["ns_id"] = ns_id

        fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

        # Setting the syslog level to 6
        command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

        command_result = self.storage_controller.peek("params/syslog/level")
        fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                      message="Checking syslog level")

        for conn_no in range(1, self.no_of_nvme_connect + 1):
            for i, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                test_interface = self.host_info[host_name]["test_interface"].name
                nqn = self.vol_list[i]["nqn"]
                if conn_no == 1:
                    host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                    host_handle.sudo_command("/etc/init.d/irqbalance stop")
                    irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")

                    if "dead" in irq_bal_stat:
                        fun_test.log("IRQ balance stopped on {}".format(i))
                    else:
                        fun_test.log("IRQ balance not stopped on {}".format(i))
                        install_status = host_handle.install_package("tuned")
                        fun_test.test_assert(install_status, "tuned installed successfully")

                        host_handle.sudo_command(
                            "tuned-adm profile network-throughput && tuned-adm active")

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

                pcap_file = "/tmp/SWOS-5844-{}_nvme_connect_auto_{}.pcap".format(host_name, conn_no)
                pcap_pid = host_handle.tcpdump_capture_start(interface=test_interface,
                                                             tcpdump_filename=pcap_file, snaplen=1500)
                nvme_connect_failed = False

                try:
                    if hasattr(self, "nvme_io_q"):
                        command_result = host_handle.sudo_command(
                            "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                                unicode.lower(self.transport_type),
                                self.test_network["f1_loopback_ip"],
                                self.transport_port,
                                nqn,
                                self.nvme_io_q,
                                self.host_ips[i]), timeout=60)
                    else:
                        command_result = host_handle.sudo_command(
                            "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                                self.test_network["f1_loopback_ip"],
                                                                                self.transport_port,
                                                                                nqn,
                                                                                self.host_ips[i]), timeout=60)
                except Exception as ex:
                    nvme_connect_failed = True
                    fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed,
                                                                                                pcap_file))
                    fun_test.critical(str(ex))
                fun_test.log(command_result)

                # Checking whether the NVMe connect is succeeded or not
                nvme_connect_exit_status = host_handle.exit_status()
                if nvme_connect_exit_status:
                    nvme_connect_failed = True
                    fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed,
                                                                                                pcap_file))

                fun_test.sleep("Wait for couple of seconds before taking tcpdump", 2)

                pcap_artifact_file = fun_test.get_test_case_artifact_file_name(
                    post_fix_name="{}".format(pcap_file.split('/')[-1]))
                host_handle.tcpdump_capture_stop(process_id=pcap_pid)

                if not nvme_connect_failed:
                    fun_test.log(
                        "nvme connect on host {} for iteration {} is successful".format(host_name, conn_no))
                    if conn_no == 1:
                        fun_test.scp(source_port=host_handle.ssh_port,
                                     source_username=host_handle.ssh_username,
                                     source_password=host_handle.ssh_password,
                                     source_ip=host_handle.host_ip,
                                     source_file_path=pcap_file,
                                     target_file_path=pcap_artifact_file)
                        fun_test.add_auxillary_file(
                            description="Host {} NVME connect passed pcap".format(host_name),
                            filename=pcap_artifact_file)

                else:
                    fun_test.log(
                        "nvme connect on host {} failed on iteration: {}. Check pcap file {} for errors".format(
                            host_name, conn_no, pcap_file))
                    fun_test.scp(source_port=host_handle.ssh_port,
                                 source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password,
                                 source_ip=host_handle.host_ip,
                                 source_file_path=pcap_file,
                                 target_file_path=pcap_artifact_file)
                    fun_test.add_auxillary_file(
                        description="Host {} NVME connect failed pcap".format(host_name),
                        filename=pcap_artifact_file)

                fun_test.test_assert(expression=not nvme_connect_failed,
                                     message="SWOS-5844: nvme connect passed on host {}".format(host_name))

            for i, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                nqn = self.vol_list[i]["nqn"]
                command_result = host_handle.sudo_command("nvme disconnect -n {}".format(nqn))
                fun_test.log(command_result)

    def run(self):
        pass

    def cleanup(self):
        self.fs = fun_test.shared_variables["fs_objs"][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        try:
            # Deleting the volumes
            for i in range(self.blt_count):
                lun_uuid = self.thin_uuid_list[i]
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
        except Exception as ex:
            fun_test.log("Clean-up of volumes failed.")
            fun_test.critical(str(ex))


class NVMeConnectWithSpurious(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Attempting NVMe session from the attached host at the end of every 1024K spurious "
                                      "connection in the middle 16K spurious connection",
                              steps="""
        1. Create a BLT volume and attach it to network host H1.
        2. From the network attached host establish a NVMe session with the F1, check the above volume is visible to the host and disconnect the NVMe session. 
        3. Attempt 1024 NVMe sessions from the non attached host H2.
        4. Repeat the above steps for N times
        """)

    def nvme_connect_disconect(self, host_handle, test_interface, nqn, count):
        pcap_file = "/tmp/{}_nvme_connect_auto_{}.pcap".format(self.genuine_host, count)
        pcap_pid = host_handle.tcpdump_capture_start(interface=test_interface,
                                                     tcpdump_filename=pcap_file, snaplen=1500)
        nvme_connect_failed = False

        try:
            if hasattr(self, "nvme_io_q"):
                command_result = host_handle.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                        unicode.lower(self.transport_type),
                        self.test_network["f1_loopback_ip"],
                        self.transport_port,
                        nqn,
                        self.nvme_io_q,
                        self.host_info[self.genuine_host]["ip"][0]), timeout=60)
                fun_test.log(command_result)
            else:
                command_result = host_handle.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                        self.test_network["f1_loopback_ip"],
                                                                        self.transport_port,
                                                                        nqn,
                                                                        self.host_info[self.genuine_host]["ip"][0]),
                    timeout=60)
        except Exception as ex:
            nvme_connect_failed = True
            fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed, pcap_file))
            fun_test.critical(str(ex))

        fun_test.log(command_result)

        # Checking whether the NVMe connect is succeeded or not
        nvme_connect_exit_status = host_handle.exit_status()
        if nvme_connect_exit_status:
            nvme_connect_failed = True
            fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed, pcap_file))

        fun_test.sleep("before stopping tcpdump", 2)
        pcap_artifact_file = fun_test.get_test_case_artifact_file_name(
            post_fix_name="{}".format(pcap_file.split('/')[-1]))
        host_handle.tcpdump_capture_stop(process_id=pcap_pid)

        if nvme_connect_failed:
            fun_test.log("nvme connect on host {} failed. Check pcap file {} for errors".format(self.genuine_host,
                                                                                                pcap_file))
            fun_test.scp(source_port=host_handle.ssh_port,
                         source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password,
                         source_ip=host_handle.host_ip,
                         source_file_path=pcap_file,
                         target_file_path=pcap_artifact_file)
            fun_test.add_auxillary_file(description="Host {} NVME connect failed pcap".format(self.genuine_host),
                                        filename=pcap_artifact_file)

        fun_test.test_assert(expression=not nvme_connect_failed,
                             message="{} - NVME Connect Status - Iteration {}".format(self.genuine_host, count))

        lsblk_output = host_handle.lsblk("-b")
        fun_test.simple_assert(lsblk_output, "Listing available volumes")

        # Checking that the above created BLT volume is visible to the end host
        self.host_info[self.genuine_host]["nvme_block_device_list"] = []
        volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
        for volume_name in lsblk_output:
            match = re.search(volume_pattern, volume_name)
            if match:
                self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                         str(match.group(2))
                self.host_info[self.genuine_host]["nvme_block_device_list"].append(self.nvme_block_device)
                fun_test.log("NVMe Block Device/s: {}".
                             format(self.host_info[self.genuine_host]["nvme_block_device_list"]))

        fun_test.test_assert_expected(expected=self.host_info[self.genuine_host]["num_volumes"],
                                      actual=len(self.host_info[self.genuine_host]["nvme_block_device_list"]),
                                      message="Expected NVMe devices are available")

        # Disconnecting the NVMe session
        command_result = host_handle.sudo_command("nvme disconnect -n {}".format(nqn))
        nvme_disconnect_exit_status = host_handle.exit_status()
        fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                      message="{} - NVME Disconnect Status - Iteration {}".format(self.genuine_host,
                                                                                                  count))
        fun_test.log(command_result)

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

        if not hasattr(self, "blt_count"):
            self.blt_count = 1
        if not hasattr(self, "repetition"):
            self.repetition = 16

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog_level"]
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]

        fun_test.shared_variables["blt_details"] = self.blt_details

        # Checking whether we have sufficient hosts to run the test
        fun_test.test_assert(self.attach_host + self.non_attach_host <= len(self.host_info),
                             "Sufficient host available to run the test")

        self.genuine_host = self.host_info.keys()[0]
        self.rogue_host = self.host_info.keys()[1]

        # Enabling counters
        """
        command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                              command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
        """

        # Configuring controller IP
        if not fun_test.shared_variables["blt"]["ip_cfg"]:
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")
            fun_test.shared_variables["blt"]["ip_cfg"] = True

        # Configure a BLT volume and attach the same to the first host
        self.vol_list = []
        self.thin_uuid_list = []

        for i in range(self.blt_count):
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
            self.vol_list.append(vol_details)

        fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

        self.ctrlr_uuid = []
        for i in range(self.blt_count):
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
            self.host_info[self.genuine_host]["num_volumes"] = 1
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                 format(self.thin_uuid_list[i], cur_uuid))
            self.vol_list[i]["ns_id"] = ns_id

        fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

        # Setting the syslog level
        command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

        command_result = self.storage_controller.peek("params/syslog/level")
        fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                      message="Checking syslog level")

        # Attempting NVMe session from the genuine host
        host_handle = self.host_info[self.genuine_host]["handle"]
        test_interface = self.host_info[self.genuine_host]["test_interface"].name
        nqn = self.vol_list[0]["nqn"]
        host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
        host_handle.sudo_command("/etc/init.d/irqbalance stop")
        irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")

        if "dead" in irq_bal_stat:
            fun_test.log("IRQ balance stopped on {}".format(self.genuine_host))
        else:
            fun_test.log("IRQ balance not stopped on {}".format(self.genuine_host))
            install_status = host_handle.install_package("tuned")
            fun_test.test_assert(install_status, "tuned installed successfully")

            host_handle.sudo_command(
                "tuned-adm profile network-throughput && tuned-adm active")

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

        self.nvme_connect_disconect(host_handle, test_interface, nqn, 0)

        """
        pcap_file = "/tmp/{}_nvme_connect_auto_0.pcap".format(self.genuine_host)
        pcap_pid = host_handle.tcpdump_capture_start(interface=test_interface,
                                                     tcpdump_filename=pcap_file, snaplen=1500)
        nvme_connect_failed = False

        try:
            if hasattr(self, "nvme_io_q"):
                command_result = host_handle.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                        unicode.lower(self.transport_type),
                        self.test_network["f1_loopback_ip"],
                        self.transport_port,
                        nqn,
                        self.nvme_io_q,
                        self.host_info[self.genuine_host]["ip"][0]), timeout=60)
                fun_test.log(command_result)
            else:
                command_result = host_handle.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                        self.test_network["f1_loopback_ip"],
                                                                        self.transport_port,
                                                                        nqn,
                                                                        self.host_info[self.genuine_host]["ip"][0]),
                    timeout=60)
        except Exception as ex:
            nvme_connect_failed = True
            fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed, pcap_file))
            fun_test.critical(str(ex))

        fun_test.log(command_result)

        # Checking whether the NVMe connect is succeeded or not
        nvme_connect_exit_status = host_handle.exit_status()
        if nvme_connect_exit_status:
            nvme_connect_failed = True
            fun_test.log("NVME connect failed - the status {} and pcap file  {}".format(nvme_connect_failed, pcap_file))

        fun_test.sleep("before stopping tcpdump", 2)
        pcap_artifact_file = fun_test.get_test_case_artifact_file_name(
            post_fix_name="{}".format(pcap_file.split('/')[-1]))
        host_handle.tcpdump_capture_stop(process_id=pcap_pid)

        if nvme_connect_failed:
            fun_test.log("nvme connect on host {} failed. Check pcap file {} for errors".format(self.genuine_host,
                                                                                                pcap_file))
            fun_test.scp(source_port=host_handle.ssh_port,
                         source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password,
                         source_ip=host_handle.host_ip,
                         source_file_path=pcap_file,
                         target_file_path=pcap_artifact_file)
            fun_test.add_auxillary_file(description="Host {} NVME connect failed pcap".format(self.genuine_host),
                                        filename=pcap_artifact_file)

        fun_test.test_assert(expression=not nvme_connect_failed,
                             message="{} - NVME Connect Status".format(self.genuine_host))

        lsblk_output = host_handle.lsblk("-b")
        fun_test.simple_assert(lsblk_output, "Listing available volumes")

        # Checking that the above created BLT volume is visible to the end host
        self.host_info[self.genuine_host]["nvme_block_device_list"] = []
        volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
        for volume_name in lsblk_output:
            match = re.search(volume_pattern, volume_name)
            if match:
                self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                         str(match.group(2))
                self.host_info[self.genuine_host]["nvme_block_device_list"].append(self.nvme_block_device)
                fun_test.log("NVMe Block Device/s: {}".
                             format(self.host_info[self.genuine_host]["nvme_block_device_list"]))

        fun_test.test_assert_expected(expected=self.host_info[self.genuine_host]["num_volumes"],
                                      actual=len(self.host_info[self.genuine_host]["nvme_block_device_list"]),
                                      message="Expected NVMe devices are available")

        # Disconnecting the NVMe session
        command_result = host_handle.sudo_command("nvme disconnect -n {}".format(nqn))
        fun_test.log(command_result)
        """

    def run(self):

        testcase = self.__class__.__name__
        self.genuine_host_handle = self.host_info[self.genuine_host]["handle"]
        self.rogue_host_handle = self.host_info[self.rogue_host]["handle"]
        test_interface = self.host_info[self.genuine_host]["test_interface"].name
        nqn = self.vol_list[0]["nqn"]

        spurious_connect_cmd = 'for i in `seq 1 {}`; do echo -n "Attempt - $i "; sudo nvme connect -t {} -a {} ' \
                               '-s {} -n {} -i 16 -q {}; done'.format(self.spurious_conn,
                                                                      unicode.lower(self.transport_type),
                                                                      self.test_network["f1_loopback_ip"],
                                                                      self.transport_port,
                                                                      nqn,
                                                                      self.host_info[self.rogue_host]["ip"][0])

        for i in range(1, self.repetition+1):
            spurious_connect_status = self.rogue_host_handle.sudo_command(command=spurious_connect_cmd, timeout=600)
            fun_test.test_assert_expected(expected=self.spurious_conn,
                                          actual=spurious_connect_status.count("Connection refused"),
                                          message="{} spurious connection from {} rejected".format(self.spurious_conn,
                                                                                                   self.rogue_host))
            self.nvme_connect_disconect(self.genuine_host_handle, test_interface, nqn, i)

    def cleanup(self):
        self.fs = fun_test.shared_variables["fs_objs"][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        try:
            # Deleting the volumes
            for i in range(self.blt_count):
                lun_uuid = self.thin_uuid_list[i]
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
        except Exception as ex:
            fun_test.log("Clean-up of volumes failed.")
            fun_test.critical(str(ex))


if __name__ == "__main__":
    bltscript = MultiHostVolumePerformanceScript()
    bltscript.add_test_case(MultiNvmeConnect())
    bltscript.add_test_case(NVMeConnectWithSpurious())
    bltscript.run()
