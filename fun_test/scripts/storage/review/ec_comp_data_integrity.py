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
Script to check data integrity of Erasure Coded volume using FIO
'''


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
        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_objs
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
            csi_perf_host_instance = Linux(host_ip=self.csi_perf_host_obj.spec["host_ip"],
                                           ssh_username=self.csi_perf_host_obj.spec["ssh_username"],
                                           ssh_password=self.csi_perf_host_obj.spec["ssh_password"])
            ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
            fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                 format(self.perf_listener_host_name, self.csi_f1_ip))

    def cleanup(self):
        #come_reboot = False
        pass
        #Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
        '''
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
            pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

            fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                         source_file_path="/tmp/nvme_connect.pcap", target_file_path=pcap_artifact_file)
            fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                        filename=pcap_artifact_file)
        '''

class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        self.sc_lock = Lock()
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
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            if not isinstance(self.csi_perf_iodepth, list):
                self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

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



    def run(self):

        testcase = self.__class__.__name__
        #test_method = testcase[4:]
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
                                                                           remote_ip=self.host_info[host_name]["ip"],
                                                                           subsys_nqn=self.nvme_subsystem,
                                                                           host_nqn=self.host_info[host_name]["ip"],
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
                    if not hasattr(self, "nvme_io_queues") or (
                            hasattr(self, "nvme_io_queues") and self.nvme_io_queues == 0):
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.attach_transport,
                            hostnqn=self.host_info[host_name]["ip"])
                    else:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.attach_transport,
                            nvme_io_queues=self.nvme_io_queues,
                            hostnqn=self.host_info[host_name]["ip"])

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


        for index, host_name in enumerate(self.host_info):
            host_handle = self.host_info[host_name]["handle"]
            fio_wr_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                 cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                 **self.fio_write_cmd_args)
            fun_test.log("FIO write Command Output:\n{}".format(fio_wr_output))
            fun_test.test_assert(fio_wr_output, "Volume write with verify=md5 on host {}".format(host_name))

            fio_rd_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                 cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                 **self.fio_read_cmd_args)
            fun_test.log("FIO read Command Output:\n{}".format(fio_rd_output))
            fun_test.test_assert(fio_wr_output, "Volume read with verify=md5 on host {}".format(host_name))

    def cleanup(self):
        #self.stats_obj.stop(self.stats_collect_details)
        self.storage_controller.verbose = False
        come_reboot = False
        if fun_test.shared_variables["ec"]["setup_created"]:
            #self.fs = self.fs_objs[0]
            self.fs = fun_test.shared_variables["fs_obj"][0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
            try:
                self.ec_info = fun_test.shared_variables["ec_info"]
                self.attach_transport = fun_test.shared_variables["attach_transport"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nvme_subsystem = fun_test.shared_variables["nvme_subsystem"]

                # Executing NVMe disconnect from all the hosts
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
                #for host_name in self.host_info:
                for host_name in fun_test.shared_variables["host_info"]:
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
                fun_test.shared_variables["ec"]["setup_created"] = False
                self.host_info[host_name]["num_volumes"] = 0
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.shared_variables["ec"]["setup_created"] = False
                self.host_info[host_name]["num_volumes"] = 0
                come_reboot = True


class DataIntegrityEffort1(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Data integrity check on EC Vol with compression effort=1",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort1, self).setup()

    def run(self):
        super(DataIntegrityEffort1, self).run()

    def cleanup(self):
        super(DataIntegrityEffort1, self).cleanup()

class DataIntegrityEffort2(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Data integrity check on EC Vol with compression effort=2",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort2, self).setup()

    def run(self):
        super(DataIntegrityEffort2, self).run()

    def cleanup(self):
        super(DataIntegrityEffort2, self).cleanup()


class DataIntegrityEffort3(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Data integrity check on EC Vol with compression effort=3",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort3, self).setup()

    def run(self):
        super(DataIntegrityEffort3, self).run()

    def cleanup(self):
        super(DataIntegrityEffort3, self).cleanup()


class DataIntegrityEffort4(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Data integrity check on EC Vol with compression effort=4",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort4, self).setup()

    def run(self):
        super(DataIntegrityEffort4, self).run()

    def cleanup(self):
        super(DataIntegrityEffort4, self).cleanup()


class DataIntegrityEffort5(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Data integrity check on EC Vol with compression effort=5",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort5, self).setup()

    def run(self):
        super(DataIntegrityEffort5, self).run()

    def cleanup(self):
        super(DataIntegrityEffort5, self).cleanup()


class DataIntegrityEffort6(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Data integrity check on EC Vol with compression effort=6",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort6, self).setup()

    def run(self):
        super(DataIntegrityEffort6, self).run()

    def cleanup(self):
        super(DataIntegrityEffort6, self).cleanup()


class DataIntegrityEffort7(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Data integrity check on EC Vol with compression effort=7",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort7, self).setup()

    def run(self):
        super(DataIntegrityEffort7, self).run()

    def cleanup(self):
        super(DataIntegrityEffort7, self).cleanup()


class DataIntegrityEffort8(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Data integrity check on EC Vol with compression effort=8",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create a 4:2 EC volume
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run FIO with verify data integrity
        """)

    def setup(self):
        super(DataIntegrityEffort8, self).setup()

    def run(self):
        super(DataIntegrityEffort8, self).run()

    def cleanup(self):
        super(DataIntegrityEffort8, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(DataIntegrityEffort1())
    ecscript.add_test_case(DataIntegrityEffort2())
    ecscript.add_test_case(DataIntegrityEffort3())
    ecscript.add_test_case(DataIntegrityEffort4())
    ecscript.add_test_case(DataIntegrityEffort5())
    ecscript.add_test_case(DataIntegrityEffort6())
    ecscript.add_test_case(DataIntegrityEffort7())
    ecscript.add_test_case(DataIntegrityEffort8())
    ecscript.run()
