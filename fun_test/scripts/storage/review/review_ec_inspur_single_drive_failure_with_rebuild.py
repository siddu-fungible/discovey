from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
import random
from lib.topology.topology_helper import TopologyHelper
from collections import OrderedDict
from scripts.storage.storage_helper import *
from lib.templates.storage.storage_fs_template import *

'''
Script to test single drive failure scenarios for 4:2 EC config
'''


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        script_config = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in script_config or not script_config["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = "default"
            self.command_timeout = 5
            self.retries = 24
        else:
            for k, v in script_config["GlobalSetup"].items():
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
            self.db_log_time = get_data_collection_time(tag="ec_inspur_fs_multi_drive_failure_with_rebuild")
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

            self.host_info = {}
            self.hosts_test_interfaces = {}
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
                self.host_info[host_name]["ip"].append(host_ip)
                fun_test.log("Host-IP: {}".format(host_ip))
                # Retrieving host handles
                host_instance = host_obj.get_instance()
                self.host_info[host_name]["handle"] = host_instance

            # Rebooting all the hosts in non-blocking mode before the test
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
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
            fun_test.shared_variables["topology"] = self.topology
            fun_test.shared_variables["fs_obj"] = self.fs_obj
            fun_test.shared_variables["come_obj"] = self.come_obj
            fun_test.shared_variables["f1_obj"] = self.f1_obj
            fun_test.shared_variables["sc_obj"] = self.sc_obj
            fun_test.shared_variables["f1_ips"] = self.f1_ips
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

            # Ensuring connectivity from Host to F1's
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                for index, ip in enumerate(self.f1_ips):
                    ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                    fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                         format(host_name, self.funcp_spec[0]["container_names"][index], ip))

        fun_test.shared_variables["testbed_config"] = self.testbed_config

    def cleanup(self):
        come_reboot = False
        '''
        if fun_test.shared_variables["ec"]["setup_created"]:
            if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                    self.testbed_config["workarounds"]["enable_funcp"]:
                self.fs = self.fs_obj[0]
                self.storage_controller = fun_test.shared_variables["sc_obj"][0]
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

            try:
                if come_reboot:
                    self.fs.fpga_initialize()
                    fun_test.log("Unexpected exit: Rebooting COMe to ensure next script execution won't ged affected")
                    self.fs.come_reset(max_wait_time=self.reboot_timeout)
            except Exception as ex:
                fun_test.critical(str(ex))

            self.topology.cleanup()
        '''


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
        # End of benchmarking json file parsing

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
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

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            self.fs = fun_test.shared_variables["fs_obj"]
            self.come_obj = fun_test.shared_variables["come_obj"]
            self.f1 = fun_test.shared_variables["f1_obj"][0][0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            self.f1_ips = fun_test.shared_variables["f1_ips"][0]
            self.host_info = fun_test.shared_variables["host_info"]
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
            for host_name in self.host_info:
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                           transport=self.attach_transport,
                                                                           remote_ip=self.host_info[host_name]["ip"][0],
                                                                           nqn=self.nvme_subsystem,
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
                                                                        tcpdump_filename="/tmp/nvme_connect.pcap")
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
                        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem,
                                       self.host_info[host_name]["ip"][0])
                        else:
                            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                                format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                       str(self.transport_port), self.nvme_subsystem, str(self.io_queues),
                                       self.host_info[host_name]["ip"][0])

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
                    self.host_info[host_name]["volume_name_list"] = []
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    cnt = 0
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            ctlr_id = match.group(1)
                            ns_id = match.group(2)
                            self.host_info[host_name]["nvme_block_device_list"].append(
                                self.nvme_device + ctlr_id + "n" + str(int(ns_id) + cnt))
                            self.host_info[host_name]["volume_name_list"].append(
                                self.nvme_block_device.replace("/dev/", ""))
                            '''
                            fun_test.test_assert_expected(expected=self.host_info[host_name]["volume_name_list"][-1],
                                                          actual=lsblk_output[volume_name]["name"],
                                                          message="{} device available".format(
                                                              self.host_info[host_name]["volume_name_list"][-1]))
                            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                                          message="{} device type check".format(
                                                              self.host_info[host_name]["volume_name_list"][-1]))
                            fun_test.test_assert_expected(expected=self.ec_info["attach_size"][int(ns_id) - 1],
                                                          actual=lsblk_output[volume_name]["size"],
                                                          message="{} volume size check".format(
                                                              self.host_info[host_name]["volume_name_list"][-1]))
                            '''
                            print('expected=self.host_info[host_name]["volume_name_list"][-1] = {}, '
                                  'actual=lsblk_output[volume_name]["name"] = {}'.format(
                                self.host_info[host_name]["volume_name_list"][-1], lsblk_output[volume_name]["name"]))
                            print('expected="disk", actual=lsblk_output[volume_name]["type"]={}'.format(
                                lsblk_output[volume_name]["type"]))
                            print('expected=self.ec_info["attach_size"][int(ns_id) - 1] = {}, '
                                  'actual=lsblk_output[volume_name]["size"] = {}'.format(
                                self.ec_info["attach_size"][int(ns_id) - 1], lsblk_output[volume_name]["size"]))
                            cnt += 1

                            # self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                            #                          str(match.group(2))
                            # self.host_info[host_name]["nvme_block_device_list"].append(self.nvme_block_device)
                            # fun_test.log("NVMe Block Device/s: {}".
                            #              format(self.host_info[host_name]["nvme_block_device_list"]))

                    try:
                        fun_test.test_assert_expected(expected=self.host_info[host_name]["num_volumes"],
                                                      actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                                      message="Expected NVMe devices are available")
                    except Exception as ex:
                        fun_test.critical(str(ex))
                    fun_test.shared_variables["ec"][host_name]["nvme_connect"] = True

                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["fio_filename"] = \
                        ":".join(self.host_info[host_name]["nvme_block_device_list"])
                    fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

            # Stopping the packet capture and Disable the udev daemon which will skew the read stats of the volume
            # during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if pcap_started[host_name]:
                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                    pcap_stopped[host_name] = True
                for service in udev_services:
                    service_status = host_handle.systemctl(service_name=service, action="stop")
                    fun_test.test_assert(service_status, "Stopping {} service in host: {}".format(service, host_name))

            # Setting the syslog level
            if self.syslog_level != "default":
                command_result = self.storage_controller.poke(
                    props_tree=["params/syslog/level", self.syslog_level],
                    legacy=False, command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Setting syslog level to {}".format(self.syslog_level))

                command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

    def run(self):

        # Test Preparation
        # Checking whether the ec_info is having the drive and device ID for the EC's plex volumes
        # Else going to extract the same
        if "device_id" not in self.ec_info:
            fun_test.log("Drive and Device ID of the EC volume's plex volumes are not available in the ec_info..."
                         "So going to pull that info")
            self.ec_info["drive_uuid"] = {}
            self.ec_info["device_id"] = {}
            for num in xrange(self.ec_info["num_volumes"]):
                self.ec_info["drive_uuid"][num] = []
                self.ec_info["device_id"][num] = []
                for blt_uuid in self.ec_info["uuids"][num]["blt"]:
                    blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid,
                                                             "stats")
                    blt_stats = self.storage_controller.peek(blt_props_tree)
                    fun_test.simple_assert(blt_stats["status"], "Stats of BLT Volume {}".format(blt_uuid))
                    if "drive_uuid" in blt_stats["data"]:
                        self.ec_info["drive_uuid"][num].append(blt_stats["data"]["drive_uuid"])
                    else:
                        fun_test.simple_assert(blt_stats["data"].get("drive_uuid"), "Drive UUID of BLT volume {}".
                                               format(blt_uuid))
                    drive_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                               "drives", blt_stats["data"]["drive_uuid"])
                    drive_stats = self.storage_controller.peek(drive_props_tree)
                    fun_test.simple_assert(drive_stats["status"], "Stats of the drive {}".
                                           format(blt_stats["data"]["drive_uuid"]))
                    if "drive_id" in drive_stats["data"]:
                        self.ec_info["device_id"][num].append(drive_stats["data"]["drive_id"])
                    else:
                        fun_test.simple_assert(drive_stats["data"].get("drive_id"), "Device ID of the drive {}".
                                               format(blt_stats["data"]["drive_uuid"]))

        fun_test.log("EC plex volumes UUID      : {}".format(self.ec_info["uuids"][0]["blt"]))
        fun_test.log("EC plex volumes drive UUID: {}".format(self.ec_info["drive_uuid"][0]))
        fun_test.log("EC plex volumes device ID : {}".format(self.ec_info["device_id"][0]))
        print("1. self.ec info: {}".format(self.ec_info))

        iostat_pid = {}
        iostat_artifact_file = {}
        start_stats = True

        for index, host_name in enumerate(self.host_info):
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            volume_name_list = self.host_info[host_name]["volume_name_list"]

            # Creating the filesystem in the volumes configured and available to the host
            if self.fs_type == "xfs":
                install_status = host_handle.install_package("xfsprogs")
                fun_test.test_assert(install_status, "Installing XFS Package")

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                size = self.ec_info["attach_size"][num]
                # Set the timeout for the filesystem create command based on its size
                fs_create_timeout = (size / self.f1_fs_timeout_ratio[0]) * self.f1_fs_timeout_ratio[1]
                if fs_create_timeout < self.min_timeout:
                    fs_create_timeout = self.min_timeout
                fs_status = host_handle.create_filesystem(self.fs_type, nvme_block_device_list[num],
                                                          timeout=fs_create_timeout)
                fun_test.test_assert(fs_status, "Creating {} filesystem on EC volume {}".
                                     format(self.fs_type, volume_name_list[num]))
                # Creating mount point
                mount_point = self.mount_path + str(num + 1)
                command_result = host_handle.create_directory(mount_point)
                fun_test.test_assert(command_result, "Creating mount point directory {}".format(mount_point))
                # Mounting the volume into the mount point
                command_result = host_handle.mount_volume(nvme_block_device_list[num], mount_point)
                fun_test.simple_assert(command_result, "Mounting EC volume {} on {}".
                                       format(nvme_block_device_list[num], mount_point))
                lsblk_output = host_handle.lsblk("-b")
                fun_test.test_assert_expected(expected=mount_point,
                                              actual=lsblk_output[volume_name_list[num]]["mount_point"],
                                              message="Mounting EC volume {} on {}".format(nvme_block_device_list[num],
                                                                                           mount_point))

            # Creating input file
            self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

            # Write a file into the EC volume of size self.test_file_size bytes
            return_size = host_handle.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
            fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                          format(self.test_file_size))
            self.src_md5sum = host_handle.md5sum(file_name=self.dd_create_file["output_file"],
                                                 timeout=self.dd_create_file["count"])
            fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                                 format(self.dd_create_file["output_file"]))

            # Test Preparation Done
            # Starting the test
            cp_timeout = (self.test_file_size / self.fs_cp_timeout_ratio[0]) * self.fs_cp_timeout_ratio[1]
            if cp_timeout < self.min_timeout:
                cp_timeout = self.min_timeout

            if hasattr(self, "back_pressure") and self.back_pressure:
                # Start the vdbench here to produce the back pressure
                pass

            # Copying the file into the all the test volumes
            source_file = self.dd_create_file["output_file"]
            dst_file1 = []

            # Calling the iostat method to collect the iostat for the while performing IO (copying file)
            iostat_count = cp_timeout / self.iostat_args["interval"]
            fun_test.log("Collecting iostat in {}".format(host_name))
            if start_stats:
                iostat_post_fix_name = "{}_iostat_fail_drive.txt".format(host_name)
                iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                    post_fix_name=iostat_post_fix_name)
                iostat_pid[host_name] = host_handle.iostat(output_file=self.iostat_args["output_file"],
                                                           interval=self.iostat_args["interval"],
                                                           count=int(iostat_count))
            else:
                fun_test.critical("Not starting the iostat collection because of lack of interval and count details")

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                dst_file1.append(self.mount_path + str(num + 1) + "/file1")
                cp_cmd = "sudo cp {} {}".format(source_file, dst_file1[-1])
                host_handle.start_bg_process(command=cp_cmd)

            # Check whether the drive failure needs to be triggered
            if hasattr(self, "trigger_drive_failure") and self.trigger_drive_failure:
                # Sleep for sometime before triggering the drive failure
                wait_time = 2
                if hasattr(self, "failure_start_time_ratio"):
                    wait_time = int(round(cp_timeout * self.failure_start_time_ratio))
                fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".format(wait_time),
                               seconds=wait_time)
                # Check whether the drive index to be failed is given or not. If not pick a random one
                if self.failure_mode == "random" or not hasattr(self, "failure_drive_index"):
                    self.failure_drive_index = []
                    for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                        self.failure_drive_index.append(random.randint(0, self.ec_info["ndata"] +
                                                                       self.ec_info["nparity"] - 1))
                # Triggering the drive failure
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    fail_uuid = self.ec_info["uuids"][num]["blt"][
                        self.failure_drive_index[num - self.test_volume_start_index]]
                    fail_device = self.ec_info["device_id"][num][
                        self.failure_drive_index[num - self.test_volume_start_index]]
                    device_fail_status = self.storage_controller.disable_device(device_id=fail_device,
                                                                                command_duration=self.command_timeout)
                    fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))

                    # Validate if Device is marked as Failed
                    device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                    device_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                    fun_test.test_assert_expected(expected="DEV_FAILED_ERR_INJECT",
                                                  actual=device_stats["data"]["device state"],
                                                  message="Device ID {} is marked as Failed".format(fail_device))
                    print('Stats of device {} and device state is {}'.format(device_stats,
                                                                             device_stats["data"]["device state"]))

            print("2. self.ec info after disabling the device : {}".format(self.ec_info))
            timer = FunTimer(max_time=cp_timeout)
            while not timer.is_expired():
                fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
                output = host_handle.get_process_id_by_pattern(process_pat=cp_cmd, multiple=True)
                if not output:
                    fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file1))
                    break
            else:
                fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file1))

            host_handle.sudo_command("sync", timeout=cp_timeout / 2)
            host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)

            # Checking if iostat process is still running...If so killing it...
            iostat_pid_check = host_handle.get_process_id("iostat")
            if iostat_pid_check and int(iostat_pid_check) == int(iostat_pid[host_name]):
                host_handle.kill_process(process_id=int(iostat_pid_check))
            # Saving the iostat output to the iostat_artifact_file file
            fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                         source_file_path=self.iostat_args["output_file"],
                         target_file_path=iostat_artifact_file[host_name])
            fun_test.add_auxillary_file(description="Host {} IOStat Usage - Drive Failure".format(host_name),
                                        filename=iostat_artifact_file[host_name])

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                cur_dst_file = dst_file1[num - self.test_volume_start_index]
                dst_file_info = host_handle.ls(cur_dst_file)
                fun_test.simple_assert(dst_file_info, "Copied file {} exists".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.test_file_size, actual=dst_file_info["size"],
                                              message="Copying {} bytes file into {}".format(self.test_file_size,
                                                                                             cur_dst_file))
                self.dst_md5sum = host_handle.md5sum(file_name=cur_dst_file, timeout=cp_timeout)
                fun_test.test_assert(self.dst_md5sum, "Finding md5sum of copied file {}".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.src_md5sum, actual=self.dst_md5sum,
                                              message="Comparing md5sum of source & destination file")

            # Creating another input file
            self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

            # Write a file into the EC volume of size self.test_file_size bytes
            return_size = host_handle.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
            fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                          format(self.test_file_size))
            self.src_md5sum = host_handle.md5sum(file_name=self.dd_create_file["output_file"],
                                                 timeout=self.dd_create_file["count"])
            fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                                 format(self.dd_create_file["output_file"]))

            # Copying the file into the volume
            source_file = self.dd_create_file["output_file"]
            dst_file2 = []
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                dst_file2.append(self.mount_path + str(num + 1) + "/file2")

                # TODO : capture IOSTAT in artifact file before start copy and after copy command is done
                # Calling the iostat method to collect the iostat for the while performing IO (copying file)
                iostat_count = cp_timeout / self.iostat_args["interval"]  # Duplicate?
                fun_test.log("Collecting iostat in {}".format(host_name))
                if start_stats:
                    iostat_post_fix_name = "{}_iostat_re_enable_drive.txt".format(host_name)
                    iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=iostat_post_fix_name)
                    iostat_pid[host_name] = host_handle.iostat(output_file=self.iostat_args["output_file"],
                                                               interval=self.iostat_args["interval"],
                                                               count=int(iostat_count))
                else:
                    fun_test.critical(
                        "Not starting the iostat collection because of lack of interval and count details")

                cp_cmd = "sudo cp {} {}".format(source_file, dst_file2[-1])
                host_handle.start_bg_process(command=cp_cmd)

            fun_test.sleep(message="Sleeping for {} seconds before bringing up the failed device(s)".
                           format(wait_time), seconds=wait_time)

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                fail_uuid = self.ec_info["uuids"][num]["blt"][
                    self.failure_drive_index[num - self.test_volume_start_index]]
                fail_device = self.ec_info["device_id"][num][
                    self.failure_drive_index[num - self.test_volume_start_index]]
                device_up_status = self.storage_controller.enable_device(device_id=fail_device,
                                                                         command_duration=self.command_timeout)
                fun_test.test_assert(device_up_status["status"], "Enabling Device ID {}".format(fail_device))

                device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                device_stats = self.storage_controller.peek(device_props_tree)
                fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                fun_test.test_assert_expected(expected="DEV_ONLINE", actual=device_stats["data"]["device state"],
                                              message="Device ID {} is Enabled again".format(fail_device))
                print('Stats of device {} and device state is {}'.format(device_stats,
                                                                         device_stats["data"]["device state"]))

                # TODO Call the rebuild for same volume
                rebuild_device = self.storage_controller.plex_rebuild(
                    subcmd="ISSUE", type=self.ec_info["volume_types"]["ec"],
                    uuid=self.ec_info["uuids"][num]["ec"][self.test_volume_start_index],
                    failed_uuid=fail_uuid, spare_uuid=fail_uuid, rate=20)
                # fun_test.test_assert(rebuild_device["status"], "Rebuild failed Device ID {}".format(fail_device))
                fun_test.log("Rebuild failed Device ID {} status {}".format(fail_device, rebuild_device["status"]))

            print("3. self.ec info after re-enabling the device : {}".format(self.ec_info))
            timer = FunTimer(max_time=cp_timeout)
            while not timer.is_expired():
                fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
                output = host_handle.get_process_id_by_pattern(process_pat=cp_cmd, multiple=True)
                if not output:
                    fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file2))
                    break
            else:
                fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file2))

            host_handle.sudo_command("sync", timeout=cp_timeout / 2)
            host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)

            # Checking if iostat process is still running...If so killing it...
            iostat_pid_check = host_handle.get_process_id("iostat")
            if iostat_pid_check and int(iostat_pid_check) == int(iostat_pid[host_name]):
                host_handle.kill_process(process_id=int(iostat_pid_check))
            # Saving the iostat output to the iostat_artifact_file file
            fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                         source_file_path=self.iostat_args["output_file"],
                         target_file_path=iostat_artifact_file[host_name])
            fun_test.add_auxillary_file(description="Host {} IOStat Usage - Drive Re-enabled".format(host_name),
                                        filename=iostat_artifact_file[host_name])

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                cur_dst_file = dst_file2[num - self.test_volume_start_index]
                dst_file_info = host_handle.ls(cur_dst_file)
                fun_test.simple_assert(dst_file_info, "Copied file {} exists".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.test_file_size, actual=dst_file_info["size"],
                                              message="Copying {} bytes file into {}".format(self.test_file_size,
                                                                                             cur_dst_file))
                self.dst_md5sum = host_handle.md5sum(file_name=cur_dst_file, timeout=cp_timeout)
                fun_test.test_assert(self.dst_md5sum, "Finding md5sum of copied file {}".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.src_md5sum, actual=self.dst_md5sum,
                                              message="Comparing md5sum of source & destination file")

    def cleanup(self):
        pass


class SingleVolumeWithoutBP(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur: 8.7.1.0: Single Drive Failure Testing without back pressure",
                              steps="""
        1. Bring up F1 in FS1600.
        2. Reboot network connected hosted and configure its test interface to establish connectivity with F1.
        3. Configure 6 BLT volumes in F1.
        4. Configure a 4:2 EC volume on top of the 6 BLT volumes.
        5. Configure a LS volume on top of the EC volume based on use_lsv config along with its associative journal 
        volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Execute NVME connect from the network host and ensure that the above volume is accessible from the host.
        8. Create ext3 filesystem in the above volume and mount the same under /mnt/ssd<volume_num>.
        9. Create test_file_size bytes file and copy the same into the above mount point.
        10. While the copy is in progress, simulate drive failure in one of the drives hosting the above 6 BLT volumes.
        11. Now configure one more BLT volume and instruct EC to use this volume to rebuild the content of the above
        failed drive.
        12. Ensure that the file is copied successfully and the md5sum between the source and destination is matching.
        13. Create another test_file_size bytes file and copy the same into the above mount point.
        14. Ensure that the file is copied successfully and the md5sum between the source and destination is matching.
        """)

    def setup(self):
        super(SingleVolumeWithoutBP, self).setup()

    def run(self):
        super(SingleVolumeWithoutBP, self).run()

    def cleanup(self):
        super(SingleVolumeWithoutBP, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(SingleVolumeWithoutBP())
    ecscript.run()
