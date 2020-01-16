from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
import random
from lib.topology.topology_helper import TopologyHelper
from collections import OrderedDict, Counter
from scripts.storage.storage_helper import *
from lib.templates.storage.storage_fs_template import *
from fun_global import PerfUnit, FunPlatform
from lib.templates.storage.storage_controller_api import *

'''
Script to test single drive failure scenarios for 4:2 EC config
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def add_to_data_base(value_dict):
    unit_dict = {"base_file_copy_time_unit": PerfUnit.UNIT_SECS, "copy_time_during_plex_fail_unit": PerfUnit.UNIT_SECS,
                 "file_copy_time_during_rebuild_unit": PerfUnit.UNIT_SECS, "plex_rebuild_time_unit": PerfUnit.UNIT_SECS}

    model_name = "InspurSingleDiskFailurePerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))


class DurableVolScript(FunTestScript):
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
            self.syslog = "default"
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
        self = single_fs_setup(self)
        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_objs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["sc_api"] = self.sc_api

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

    def cleanup(self):
        if fun_test.shared_variables["ec"]["setup_created"]:
            try:
                # self.ec_info = fun_test.shared_variables["ec_info"]
                # self.attach_transport = fun_test.shared_variables["attach_transport"]
                # self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.volume_uuid_list = fun_test.shared_variables["volume_uuid_list"]
                self.subsys_nqn_list = fun_test.shared_variables["subsys_nqn_list"]

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
                for index, host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.subsys_nqn_list[index])
                    host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="{} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                for index, vol_uuid in enumerate(self.volume_uuid_list):
                    # Detaching volume
                    detach_volume = self.sc_api.detach_volume(port_uuid=vol_uuid)
                    fun_test.log("Detach volume API response: {}".format(detach_volume))
                    fun_test.test_assert(detach_volume["status"], "Detach Volume {}".format(vol_uuid))

                    # Deleting volume
                    delete_volume = self.sc_api.delete_volume(vol_uuid=vol_uuid)
                    fun_test.test_assert(delete_volume["status"],
                                         "Deleting BLT Vol with uuid {} on DUT".format(vol_uuid))

                '''
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
                '''
            except Exception as ex:
                fun_test.critical(str(ex))


class DurableVolumeTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
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
        # End of benchmarking json file parsing

        fun_test.shared_variables["attach_transport"] = self.attach_transport
        # fun_test.shared_variables["nvme_subsystem"] = self.nvme_subsystem

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "num_volumes" in job_inputs:
            self.ec_info["num_volumes"] = job_inputs["num_volumes"]
        if "vol_size" in job_inputs:
            self.ec_info["capacity"] = job_inputs["vol_size"]
            if self.test_file_size > int(self.ec_info["capacity"] / 2):
                self.test_file_size = int(self.ec_info["capacity"] / 2)
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.fs_obj = fun_test.shared_variables["fs_obj"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.db_log_time = fun_test.shared_variables["db_log_time"]
        self.num_hosts = len(self.host_info)

        self.sc_api = fun_test.shared_variables["sc_api"]

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            '''
            # Covered as dataplane IP config
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")
            '''

            '''
            # Checking if test case is with back-pressure; if so creating additional volume for back-pressure
            if self.back_pressure:
                fun_test.log("Creating Additional EC volume for back-pressure")
                self.ec_info["num_volumes"] += 1
            '''
            # Creating pool
            if self.create_pool:
                pass
            # Fetching pool uuid as per pool name provided
            pool_name = self.default_pool if not self.create_pool else self.pool_name
            self.pool_uuid = self.sc_api.get_pool_uuid_by_name(name=pool_name)

            self.volume_uuid_list = []
            self.subsys_nqn_list = []
            self.host_nqn_list = []
            host_ips = []
            for index, host_name in enumerate(self.host_info):
                host_ips.append(self.host_info[host_name]["ip"][index])

            self.ec_info["spare_plex_uuid"] = {}
            for num in xrange(self.ec_info["num_volumes"]):
                self.ec_info["uuids"][num] = {}
                self.ec_info["spare_plex_uuid"][num] = {}
                self.ec_info["spare_plex_uuid"][num]["blt"] = []
                self.ec_info["uuids"][num]["ndata"] = []
                self.ec_info["uuids"][num]["blt"] = []

                # Create volumes
                response = self.sc_api.create_volume(self.pool_uuid, self.ec_info["volume_name"] + str(num + 1),
                                                     self.ec_info["capacity"],
                                                     self.ec_info["stripe_count"], self.ec_info["volume_types"]["ec"],
                                                     self.ec_info["encrypt"], self.ec_info["allow_expansion"],
                                                     self.ec_info["data_protection"],
                                                     self.ec_info["compression_effort"])
                fun_test.log("Create EC volume API response: {}".format(response))
                fun_test.test_assert(response["status"], "Create EC Volume {}".format(num + 1))

                # ATTACH volume
                attach_volume = self.sc_api.volume_attach_remote(vol_uuid=response["data"]["uuid"],
                                                                 transport=self.attach_transport.upper(),
                                                                 remote_ip=host_ips[num])
                fun_test.log("Attach volume API response: {}".format(attach_volume))
                fun_test.test_assert(attach_volume["status"], "Attaching EC volume {} to the host {}".
                                     format(response["data"]["uuid"], host_ips[num]))

                # Extracting the NVMe subsys nqn from the volume ATTACH response, later used in NVMe connect
                host_nqn = attach_volume["data"]["host_nqn"]
                subsys_nqn = attach_volume["data"]["subsys_nqn"] if "subsys_nqn" in attach_volume["data"] else \
                    attach_volume["data"].get("nqn")
                fun_test.simple_assert(subsys_nqn, "Extracted the Subsys NQN to which volume {} got attached".
                                       format(response["data"]["uuid"]))
                fun_test.simple_assert("host_nqn" in attach_volume["data"],
                                       "Extracted the Controller's Host NQN to which volume {} got attached".
                                       format(response["data"]["uuid"]))
                self.volume_uuid_list.append(response["data"]["uuid"])
                self.subsys_nqn_list.append(subsys_nqn)
                self.host_nqn_list.append(host_nqn)
            fun_test.shared_variables["volume_uuid_list"] = self.volume_uuid_list
            fun_test.shared_variables["subsys_nqn_list"] = self.subsys_nqn_list
            fun_test.shared_variables["host_nqn_list"] = self.host_nqn_list
            fun_test.shared_variables["ec"]["setup_created"] = True

            if self.rebuild_on_spare_volume:
                # Create spare plex volumes
                for i in xrange(self.plex_failure_count):
                    create_spare_plex = self.sc_api.create_volume(pool_uuid=self.pool_uuid, name="thin_block" + str(i + 1),
                                                               capacity=self.blt_details["capacity"],
                                                               vol_type=self.blt_details["type"],
                                                               stripe_count=self.blt_details["stripe_count"])
                    fun_test.log("Create Spare plex API response: {}".format(create_spare_plex))
                    fun_test.test_assert(create_spare_plex["status"], "Create Spare plex {} with uuid {} on DUT".
                                         format(i + 1, create_spare_plex["data"]["uuid"]))
                    self.thin_uuid_list.append(create_spare_plex["data"]["uuid"])
                fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
                num = self.test_volume_start_index
                self.ec_info["spare_plex_uuid"][num]["blt"].append(create_spare_plex["data"]["uuid"])

            '''
            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))
            if self.rebuild_on_spare_volume:
                num = self.test_volume_start_index
                vtype = "ndata"
                self.spare_vol_uuid = utils.generate_uuid()
                self.ec_info["uuids"][num][vtype].append(self.spare_vol_uuid)
                self.ec_info["uuids"][num]["blt"].append(self.spare_vol_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.ec_info["volume_types"][vtype], capacity=self.ec_info["volume_capacity"][num][vtype],
                    block_size=self.ec_info["volume_block"][vtype], name=vtype + "_" + self.spare_vol_uuid[-4:],
                    uuid=self.spare_vol_uuid, group_id=num + 1, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(
                    command_result["status"], "Creating Spare Volume {} {} {} {} bytes volume on DUT instance".
                        format(num, vtype, self.ec_info["volume_types"][vtype],
                               self.ec_info["volume_capacity"][num][vtype]))

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            # Attaching/Exporting all the EC/LS volumes to the external server
            self.ctrlr_uuid = []
            for host_name in self.host_info:
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_id=0,
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
            '''

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

            for index, host_name in enumerate(self.host_info):
                fun_test.shared_variables["ec"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]

                host_nqn_workaround = True
                if host_nqn_workaround:
                    host_nqn_val = self.subsys_nqn_list[index].split(":")[0] + ":" + self.host_nqn_list[index]
                else:
                    host_nqn_val = self.host_nqn_list[index]

                if not fun_test.shared_variables["ec"]["nvme_connect"]:
                    if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {} -Q {}".format(
                            self.attach_transport.lower(),
                            self.test_network["f1_loopback_ip"],
                            self.transport_port,
                            self.subsys_nqn_list[index],
                            self.nvme_io_queues, host_nqn_val,
                            self.queue_size)
                        fun_test.log(nvme_connect_cmd)
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}".format(
                            self.attach_transport.lower(),
                            self.test_network["f1_loopback_ip"],
                            self.transport_port,
                            self.subsys_nqn_list[index],
                            host_nqn_val)
                        fun_test.log(nvme_connect_cmd)
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

                    # Checking that the above created EC volume is visible to the end host after NVME connect
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    self.host_info[host_name]["nvme_block_device_list"] = []
                    self.host_info[host_name]["volume_name_list"] = []
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            ctlr_id = match.group(1)
                            ns_id = match.group(2)
                            self.host_info[host_name]["nvme_block_device_list"].append(
                                self.nvme_device + ctlr_id + "n" + ns_id)
                            self.host_info[host_name]["volume_name_list"].append(
                                self.nvme_block_device.replace("/dev/", ""))

                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["volume_name_list"].sort()
                    # Total number of volumes available should be equal to the ec_info["num_volumes"]
                    fun_test.test_assert_expected(expected=self.ec_info["num_volumes"],
                                                  actual=len(self.host_info[host_name]["volume_name_list"]),
                                                  message="Number of volumes available")
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
            if self.syslog != "default":
                command_result = self.storage_controller.poke(
                    props_tree=["params/syslog/level", self.syslog],
                    legacy=False, command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Setting syslog level to {}".format(self.syslog))

                command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

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

        fun_test.log("EC plex volumes UUID      : {}".format(self.ec_info["uuids"][self.test_volume_start_index]["blt"]))
        fun_test.log("EC plex volumes drive UUID: {}".format(self.ec_info["drive_uuid"][self.test_volume_start_index]))
        fun_test.log("EC plex volumes device ID : {}".format(self.ec_info["device_id"][self.test_volume_start_index]))

        self.ec_info = fun_test.shared_variables["ec_info"]
        self.vol_details = fun_test.shared_variables["vol_details"]
        # Checking whether the job's inputs argument is having the list of io_depths to be used in this test.
        # If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_output = {}
        test_thread_id = {}
        host_clone = {}
        size = (self.ec_info["capacity"] * self.ec_info["num_volumes"]) / (1024 ** 3)

        # Writing first 50% of volume with --verify=md5
        for index, host_name in enumerate(self.host_info):
            start_time = time.time()
            fio_job_args = ""
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            self.fio_write_cmd_args["offset"] = "0%"
            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()
            fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                         format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"], self.fio_write_cmd_args["iodepth"]))

            test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                  func=fio_parser,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  iodepth=self.fio_write_cmd_args["iodepth"],
                                                                  rw=self.fio_write_cmd_args["rw"],
                                                                  bs=self.fio_write_cmd_args["bs"],
                                                                  name="{}_{}".format(host_name, self.fio_write_cmd_args["rw"]),
                                                                  **self.fio_write_cmd_args)
            end_time = time.time()
            time_taken = end_time - start_time
            fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Triggering drive failure
        if hasattr(self, "trigger_failure") and self.trigger_failure:
            # Sleep for sometime before triggering the drive failure
            wait_time = 2
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
                if self.fail_drive:
                    ''' Marking drive as failed '''
                    # Inducing failure in drive
                    fun_test.log("Initiating drive failure")
                    device_fail_status = self.storage_controller.disable_device(
                        device_id=fail_device, command_duration=self.command_timeout)
                    fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))
                    # Validate if Device is marked as Failed
                    device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                    device_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                    fun_test.test_assert_expected(expected="DEV_ERR_INJECT_ENABLED",
                                                  actual=device_stats["data"]["device state"],
                                                  message="Device ID {} is marked as Failed".format(fail_device))
                    ''' Marking drive as failed '''
                else:
                    ''' Marking Plex as failed '''
                    # Inducing failure in one of the Plex of the volume
                    fun_test.log("Initiating Plex failure")
                    volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                    fun_test.test_assert(volume_fail_status["status"], "Disabling Plex UUID {}".format(fail_uuid))
                    # Validate if volume is marked as Failed
                    device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                             fail_uuid)
                    volume_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.test_assert_expected(
                        expected=1, actual=volume_stats["data"]["stats"]["fault_injection"],
                        message="Plex is marked as Failed")
                    ''' Marking Plex as failed '''

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        # Verifying data integrity after Write is complete
        for index, host_name in enumerate(self.host_info):
            start_time = time.time()
            fio_job_args = ""
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()

            # Verifying Data Integrity for 50% data written to the volume with --verify=md5
            self.fio_verify_cmd_args["offset"] = "0%"
            fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                         format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"], self.fio_verify_cmd_args["iodepth"]))

            test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                  func=fio_parser,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  iodepth=self.fio_verify_cmd_args["iodepth"],
                                                                  rw=self.fio_verify_cmd_args["rw"],
                                                                  bs=self.fio_verify_cmd_args["bs"],
                                                                  name="{}_{}".format(host_name, self.fio_verify_cmd_args["rw"]),
                                                                  **self.fio_verify_cmd_args)
            end_time = time.time()
            time_taken = end_time - start_time
            fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))

        # Writing remaining 50% of volume with --verify=md5
        for index, host_name in enumerate(self.host_info):
            start_time = time.time()
            fio_job_args = ""
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()
            self.fio_write_cmd_args["offset"] = "50%"
            fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                         format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                self.fio_write_cmd_args["iodepth"]))

            test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                  func=fio_parser,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  iodepth=self.fio_write_cmd_args["iodepth"],
                                                                  rw=self.fio_write_cmd_args["rw"],
                                                                  bs=self.fio_write_cmd_args["bs"],
                                                                  name="{}_{}".format(host_name,
                                                                                      self.fio_write_cmd_args[
                                                                                          "rw"]),
                                                                  **self.fio_write_cmd_args)
            end_time = time.time()
            time_taken = end_time - start_time
            fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Triggering Plex rebuild
        fun_test.sleep(message="Sleeping for {} seconds before before bringing up the failed device(s) & "
                               "plex rebuild".format(wait_time), seconds=wait_time)
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            fail_uuid = self.ec_info["uuids"][num]["blt"][
                self.failure_drive_index[num - self.test_volume_start_index]]
            fail_device = self.ec_info["device_id"][num][
                self.failure_drive_index[num - self.test_volume_start_index]]

            if not self.rebuild_on_spare_volume:
                if self.fail_drive:
                    ''' Marking drive as online '''
                    device_up_status = self.storage_controller.enable_device(device_id=fail_device,
                                                                             command_duration=self.command_timeout)
                    fun_test.test_assert(device_up_status["status"], "Enabling Device ID {}".format(fail_device))

                    device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                    device_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                    fun_test.test_assert_expected(expected="DEV_ONLINE",
                                                  actual=device_stats["data"]["device state"],
                                                  message="Device ID {} is Enabled again".format(fail_device))
                    ''' Marking drive as online '''
                else:
                    ''' Marking Plex as online '''
                    volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                    fun_test.test_assert(volume_fail_status["status"], "Re-enabling Volume UUID {}".
                                         format(fail_uuid))
                    # Validate if Volume is enabled again
                    device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                             fail_uuid)
                    volume_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.test_assert_expected(expected=0,
                                                  actual=volume_stats["data"]["stats"]["fault_injection"],
                                                  message="Plex is marked as online")
                    ''' Marking Plex as online '''

            # Rebuild failed plex
            if self.rebuild_on_spare_volume:
                spare_uuid = self.spare_vol_uuid
                fun_test.log("Rebuilding on spare volume: {}".format(spare_uuid))
            else:
                spare_uuid = fail_uuid
                fun_test.log("Rebuilding on failed volume: {}".format(spare_uuid))
            rebuild_device = self.storage_controller.plex_rebuild(
                subcmd="ISSUE", type=self.ec_info["volume_types"]["ec"],
                uuid=self.ec_info["uuids"][num]["ec"][num - self.test_volume_start_index],
                failed_uuid=fail_uuid, spare_uuid=spare_uuid, rate=self.rebuild_rate)
            fun_test.test_assert(rebuild_device["status"], "Rebuild failed Plex {}".format(fail_uuid))
            fun_test.log("Rebuild failed Plex {} status {}".format(fail_uuid, rebuild_device["status"]))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        # Verifying data integrity after Write is complete
        for index, host_name in enumerate(self.host_info):
            start_time = time.time()
            fio_job_args = ""
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()
            self.fio_verify_cmd_args["offset"] = "50%"
            # Writing 50% of volume with --verify=md5
            fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                         format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                self.fio_verify_cmd_args["iodepth"]))

            test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                  func=fio_parser,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  iodepth=self.fio_verify_cmd_args["iodepth"],
                                                                  rw=self.fio_verify_cmd_args["rw"],
                                                                  bs=self.fio_verify_cmd_args["bs"],
                                                                  name="{}_{}".format(host_name,
                                                                                      self.fio_verify_cmd_args[
                                                                                          "rw"]),
                                                                  **self.fio_verify_cmd_args)
            end_time = time.time()
            time_taken = end_time - start_time
            fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))

        # Parsing f1 uart log file to search rebuild start and finish time
        '''
        log file output:
        [2537.762236 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 under rebuild total failed:1"
        [2774.291395 2.2.3] ALERT ecvol "storage/flvm/ecvol/ecvol.c:3312:ecvol_rebuild_done_process_push() Rebuild operation complete for plex:5"
        [2774.292149 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 marked active total failed:0"
        '''
        try:
            bmc_handle = self.fs_obj[0].get_bmc()
            uart_log_file = self.fs_obj[0].get_bmc().get_f1_uart_log_filename(f1_index=self.f1_in_use)
            fun_test.log("F1 UART Log file used to check Rebuild operation status: {}".format(uart_log_file))
            search_pattern = "'under rebuild total failed'"
            output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                               timeout=self.command_timeout))
            fun_test.test_assert_expected(expected=1, actual=int(output.rstrip()),
                                          message="Rebuild operation is started")
            rebuild_start_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".format(
                search_pattern, uart_log_file, timeout=self.command_timeout))
            rebuild_start_time = int(round(float(rebuild_start_time.rstrip())))
            fun_test.log("Rebuild operation started at : {}".format(rebuild_start_time))

            timer = FunTimer(max_time=self.rebuild_timeout)
            while not timer.is_expired():
                search_pattern = "'Rebuild operation complete for plex'"
                fun_test.sleep("Waiting for plex rebuild to complete", seconds=(self.status_interval * 5))
                output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                                   timeout=self.command_timeout))
                if int(output.rstrip()) == 1:
                    rebuild_stop_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".
                                                           format(search_pattern, uart_log_file,
                                                                  timeout=self.command_timeout))
                    rebuild_stop_time = int(round(float(rebuild_stop_time.rstrip())))
                    fun_test.log("Rebuild operation completed at: {}".format(rebuild_stop_time))
                    fun_test.log("Rebuild operation on plex {} is completed".format(spare_uuid))
                    break
            else:
                fun_test.test_assert(False, "Rebuild operation on plex {} completed".format(spare_uuid))
            plex_rebuild_time = rebuild_stop_time - rebuild_start_time
            fun_test.log("Time taken to rebuild plex: {}".format(plex_rebuild_time))
        except Exception as ex:
            fun_test.critical(str(ex))

        # After Data Reconstruction is completed, verifying 100% data integrity
        for index, host_name in enumerate(self.host_info):
            start_time = time.time()
            fio_job_args = ""
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            wait_time = self.num_hosts - index
            host_clone[host_name] = self.host_info[host_name]["handle"].clone()
            self.fio_verify_cmd_args["size"] = "100%"
            self.fio_verify_cmd_args["offset"] = "0%"
            # After Data Reconstruction is completed, verifying 100% data integrity
            fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                         format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                self.fio_verify_cmd_args["iodepth"]))

            test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                  func=fio_parser,
                                                                  arg1=host_clone[host_name],
                                                                  host_index=index,
                                                                  iodepth=self.fio_verify_cmd_args["iodepth"],
                                                                  rw=self.fio_verify_cmd_args["rw"],
                                                                  bs=self.fio_verify_cmd_args["bs"],
                                                                  name="{}_{}".format(host_name,
                                                                                      self.fio_verify_cmd_args[
                                                                                          "rw"]),
                                                                  **self.fio_verify_cmd_args)
            end_time = time.time()
            time_taken = end_time - start_time
            fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))


        """
        ## Original
        for index, host_name in enumerate(self.host_info):
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            volume_name_list = self.host_info[host_name]["volume_name_list"]
            self.host_info[host_name]["src_file"] = {}
            self.host_info[host_name]["dst_file"] = {}

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
                '''
                fun_test.test_assert_expected(expected=mount_point,
                                              actual=lsblk_output[volume_name_list[num]]["mount_point"],
                                              message="Mounting EC volume {} on {}".format(nvme_block_device_list[num],
                                                                                           mount_point))
                '''

            # Setting nr_requests value tot 4, to limit request_queue (to limit flow control)
            try:
                host_handle.sudo_command("echo '{}' > /sys/block/nvme0n2/queue/nr_requests".format(self.nr_requests))
                # fun_test.simple_assert(expression=host_handle.exit_status() == 0,
                # message="nr_requests on host {} is set to: {}".format(host_name, self.nr_requests))
            except Exception as ex:
                fun_test.critical(str(ex))
            # Start background load on other volume
            if hasattr(self, "back_pressure") and self.back_pressure:
                try:
                    # Start the fio here to produce the back pressure
                    fio_pid = None
                    check_pid = None
                    self.back_pressure_io["fio_cmd_args"] += "--filename={}".\
                        format(nvme_block_device_list[self.test_volume_start_index-1])
                    fio_pid = host_handle.start_bg_process(command=self.back_pressure_io["fio_cmd_args"],
                                                           timeout=self.back_pressure_io["timeout"])
                    fun_test.test_assert(expression=fio_pid is not None, message="Back pressure is started")
                    fun_test.sleep("Allowing FIO to warmup", 10)
                    # Re-checking if FIO processes are not died due to any issue
                    check_pid = host_handle.get_process_id(process_name="fio")
                    fun_test.test_assert(expression=check_pid is not None, message="Back pressure is active")
                    fun_test.log("Back pressure is still running pid/s: {}".format(fio_pid))
                except Exception as ex:
                    fun_test.critical(str(ex))

            ''' start: base file copy to measure time without any failure or rebuild '''
            # Creating input file
            self.host_info[host_name]["src_file"]["base_file"] = {}
            self.host_info[host_name]["src_file"]["base_file"]["md5sum"] = []
            self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

            # Write a file into the EC volume of size self.test_file_size bytes
            return_size = host_handle.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
            fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes input base file".
                                          format(self.test_file_size))
            self.src_md5sum = host_handle.md5sum(file_name=self.dd_create_file["output_file"],
                                                 timeout=self.dd_create_file["count"])
            fun_test.test_assert(self.src_md5sum, "Finding md5sum of source base file {}".
                                 format(self.dd_create_file["output_file"]))
            self.host_info[host_name]["src_file"]["base_file"]["md5sum"].append(self.src_md5sum)

            # Test Preparation Done
            # Starting the test
            cp_timeout = (self.test_file_size / self.fs_cp_timeout_ratio[0]) * self.fs_cp_timeout_ratio[1]
            if cp_timeout < self.min_timeout:
                cp_timeout = self.min_timeout

            # Copying the file into the all the test volumes
            source_file = self.dd_create_file["output_file"]
            dst_file1 = []

            # Calling the iostat method to collect the iostat for the while performing IO (copying file)
            iostat_count = cp_timeout / self.iostat_args["interval"]
            fun_test.log("Collecting iostat on {}".format(host_name))
            if start_stats:
                iostat_post_fix_name = "{}_iostat_copy_base_file.txt".format(host_name)
                iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                    post_fix_name=iostat_post_fix_name)
                iostat_pid[host_name] = host_handle.iostat(
                    device=",".join(self.host_info[host_name]["nvme_block_device_list"]),
                    output_file=self.iostat_args["output_file"],
                    interval=self.iostat_args["interval"],
                    count=int(iostat_count))
            else:
                fun_test.critical("Not starting the iostat collection because of lack of interval and count details")

            fun_test.log("Performing sync operation before starting file copy")
            host_handle.sudo_command("sync", timeout=cp_timeout / 2)
            fun_test.simple_assert(expression=host_handle.exit_status() == 0,
                                   message="Sync command done before base file copy")

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                dst_file1.append(self.mount_path + str(num + 1) + "/base_file")
                cp_cmd = 'sudo sh -c "date +%s; cp {} {}; sync; date +%s"'.format(source_file, dst_file1[-1])
                cp_file_output = "{}_{}_{}.out".format(self.file_copy_output, num, self.src_md5sum[-4:])
                cp_pid = host_handle.start_bg_process(command=cp_cmd, output_file=cp_file_output)
                fun_test.log("File copy is started in background, pid is: {}".format(cp_pid))

            # Waiting till file copy completes
            timer = FunTimer(max_time=cp_timeout)
            while not timer.is_expired():
                fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
                output = host_handle.get_process_id_by_pattern(process_pat=cp_pid, multiple=True)
                if not output:
                    fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file1))
                    break
            else:
                fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file1))

            # Parsing copy time output and recording time taken to copy file
            read_output = host_handle.read_file(file_name=cp_file_output)
            lines = read_output.split("\n")
            result = {}
            for num, line in enumerate(lines):
                search_time = re.search(r'(\d+)', line)
                if search_time:
                    if re.search("([0-9].*)", search_time.group(1)):
                        result[num] = search_time.group(1)
            fun_test.log("Recorded start time: {} and end time: {} for file copy".format(result[0], result[1]))
            base_file_copy_time = int(result[1]) - int(result[0])
            fun_test.log("Base File is copied in: {} sec".format(base_file_copy_time))
            host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)
            row_data_dict["base_copy_time"] = base_file_copy_time

            # Checking if iostat process is still running...If so killing it...
            iostat_pid_check = host_handle.get_process_id("iostat")
            if iostat_pid_check and int(iostat_pid_check) == int(iostat_pid[host_name]):
                host_handle.kill_process(process_id=int(iostat_pid_check))
            # Saving the iostat output to the iostat_artifact_file file
            fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                         source_file_path=self.iostat_args["output_file"],
                         target_file_path=iostat_artifact_file[host_name])
            fun_test.add_auxillary_file(description="Host {} IOStat Usage - Base File copy".format(host_name),
                                        filename=iostat_artifact_file[host_name])

            # Validating data integrity after file copy
            self.host_info[host_name]["dst_file"]["base_file"] = {}
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                if num not in self.host_info[host_name]["dst_file"]["base_file"]:
                    self.host_info[host_name]["dst_file"]["base_file"][num] = {}
                    self.host_info[host_name]["dst_file"]["base_file"][num]["md5sum"] = []
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
                self.host_info[host_name]["dst_file"]["base_file"][num]["md5sum"].append(self.dst_md5sum)

                # Deleting the base file from local disk, to free up disk space for next test files
                try:
                    rm_cmd = "rm -f {}".format(source_file)
                    host_handle.sudo_command(command=rm_cmd)
                    fun_test.simple_assert(expression=host_handle.exit_status() == 0,
                                           message="Source base file is deleted")
                    host_handle.sudo_command("sync", timeout=cp_timeout / 2)
                    host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)
                except Exception as ex:
                    fun_test.critical(str(ex))
            ''' finish: base file copy to measure time without any failure or rebuild'''

            ''' start: File copy while the BLT volume is marked failed '''
            self.host_info[host_name]["src_file"]["file1"] = {}
            self.host_info[host_name]["src_file"]["file1"]["md5sum"] = []
            self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

            # Write a file into the EC volume of size self.test_file_size bytes
            return_size = host_handle.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
            fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                          format(self.test_file_size))
            self.src_md5sum = host_handle.md5sum(file_name=self.dd_create_file["output_file"],
                                                 timeout=self.dd_create_file["count"])
            fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                                 format(self.dd_create_file["output_file"]))
            self.host_info[host_name]["src_file"]["file1"]["md5sum"].append(self.src_md5sum)

            # Test Preparation Done
            # Starting the test
            cp_timeout = (self.test_file_size / self.fs_cp_timeout_ratio[0]) * self.fs_cp_timeout_ratio[1]
            if cp_timeout < self.min_timeout:
                cp_timeout = self.min_timeout

            # Copying the file into the all the test volumes
            source_file = self.dd_create_file["output_file"]
            dst_file1 = []

            # Calling the iostat method to collect the iostat for the while performing IO (copying file)
            iostat_count = cp_timeout / self.iostat_args["interval"]
            fun_test.log("Collecting iostat on {}".format(host_name))
            if start_stats:
                iostat_post_fix_name = "{}_iostat_copy_during_fail.txt".format(host_name)
                iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                    post_fix_name=iostat_post_fix_name)
                iostat_pid[host_name] = host_handle.iostat(
                    device=",".join(self.host_info[host_name]["nvme_block_device_list"]),
                    output_file=self.iostat_args["output_file"], interval=self.iostat_args["interval"],
                    count=int(iostat_count))
            else:
                fun_test.critical("Not starting the iostat collection because of lack of interval and count details")

            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                dst_file1.append(self.mount_path + str(num + 1) + "/file1")
                cp_cmd = 'sudo sh -c "date +%s; cp {} {}; sync; date +%s"'.format(source_file, dst_file1[-1])
                cp_file_output = "{}_{}_{}.out".format(self.file_copy_output, num, self.src_md5sum[-4:])
                cp_pid = host_handle.start_bg_process(command=cp_cmd, output_file=cp_file_output)
                fun_test.log("File copy is started in background, pid is: {}".format(cp_pid))

            # Check whether the drive failure needs to be triggered
            if hasattr(self, "trigger_failure") and self.trigger_failure:
                # Sleep for sometime before triggering the drive failure
                wait_time = 2
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
                    if self.fail_drive:
                        ''' Marking drive as failed '''
                        # Inducing failure in drive
                        fun_test.log("Initiating drive failure")
                        device_fail_status = self.storage_controller.disable_device(
                            device_id=fail_device, command_duration=self.command_timeout)
                        fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))
                        # Validate if Device is marked as Failed
                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                        fun_test.test_assert_expected(expected="DEV_ERR_INJECT_ENABLED",
                                                      actual=device_stats["data"]["device state"],
                                                      message="Device ID {} is marked as Failed".format(fail_device))
                        ''' Marking drive as failed '''
                    else:
                        ''' Marking Plex as failed '''
                        # Inducing failure in one of the Plex of the volume
                        fun_test.log("Initiating Plex failure")
                        volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                        fun_test.test_assert(volume_fail_status["status"], "Disabling Plex UUID {}".format(fail_uuid))
                        # Validate if volume is marked as Failed
                        device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                                 fail_uuid)
                        volume_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.test_assert_expected(
                            expected=1, actual=volume_stats["data"]["stats"]["fault_injection"],
                            message="Plex is marked as Failed")
                        ''' Marking Plex as failed '''

            timer = FunTimer(max_time=cp_timeout)
            while not timer.is_expired():
                fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
                output = host_handle.get_process_id_by_pattern(process_pat=cp_pid, multiple=True)
                if not output:
                    fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file1))
                    break
            else:
                fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file1))

            # Parsing copy time output and recording time taken to copy file
            read_output = host_handle.read_file(file_name=cp_file_output)
            lines = read_output.split("\n")
            result = {}
            for num, line in enumerate(lines):
                search_time = re.search(r'(\d+)', line)
                if search_time:
                    if re.search("([0-9].*)", search_time.group(1)):
                        result[num] = search_time.group(1)
            fun_test.log("Recorded start time: {} and end time: {} for file copy".format(result[0], result[1]))
            copy_time_during_plex_fail = int(result[1]) - int(result[0])
            fun_test.log("Time to copy the file during drive/plex failure: {} sec".format(copy_time_during_plex_fail))

            row_data_dict["copy_time_during_plex_fail"] = copy_time_during_plex_fail
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

            self.host_info[host_name]["dst_file"]["file1"] = {}
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                if num not in self.host_info[host_name]["dst_file"]["file1"]:
                    self.host_info[host_name]["dst_file"]["file1"][num] = {}
                    self.host_info[host_name]["dst_file"]["file1"][num]["md5sum"] = []
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
                self.host_info[host_name]["dst_file"]["file1"][num]["md5sum"].append(self.dst_md5sum)

                # Deleting the base file from local disk, to free up disk space for next test files
                try:
                    rm_cmd = "rm -f {}".format(source_file)
                    host_handle.sudo_command(command=rm_cmd)
                    fun_test.simple_assert(expression=host_handle.exit_status() == 0,
                                           message="Source base file is deleted")
                    host_handle.sudo_command("sync", timeout=cp_timeout / 2)
                    host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)
                except Exception as ex:
                    fun_test.critical(str(ex))
            ''' Finish: File copy while the BLT volume is marked failed '''

            ''' start: File copy while the BLT volume is rebuilding '''
            # Creating another input file
            self.host_info[host_name]["src_file"]["file2"] = {}
            self.host_info[host_name]["src_file"]["file2"]["md5sum"] = []
            self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

            # Write a file into the EC volume of size self.test_file_size bytes
            return_size = host_handle.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
            fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                          format(self.test_file_size))
            self.src_md5sum = host_handle.md5sum(file_name=self.dd_create_file["output_file"],
                                                 timeout=self.dd_create_file["count"])
            fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                                 format(self.dd_create_file["output_file"]))
            self.host_info[host_name]["src_file"]["file2"]["md5sum"].append(self.src_md5sum)

            # Copying the file into the volume
            source_file = self.dd_create_file["output_file"]
            dst_file2 = []
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                dst_file2.append(self.mount_path + str(num + 1) + "/file2")
                # Calling the iostat method to collect the iostat for the while performing IO (copying file)
                iostat_count = cp_timeout / self.iostat_args["interval"]  # Duplicate?
                fun_test.log("Collecting iostat on {}".format(host_name))
                if start_stats:
                    iostat_post_fix_name = "{}_iostat_copy_during_rebuild.txt".format(host_name)
                    iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=iostat_post_fix_name)
                    iostat_pid[host_name] = host_handle.iostat(
                        device=",".join(self.host_info[host_name]["nvme_block_device_list"]),
                        output_file=self.iostat_args["output_file"], interval=self.iostat_args["interval"],
                        count=int(iostat_count))
                else:
                    fun_test.critical(
                        "Not starting the iostat collection because of lack of interval and count details")

                cp_cmd = 'sudo sh -c "date +%s; cp {} {}; sync; date +%s"'.format(source_file, dst_file2[-1])
                cp_file_output = "{}_{}_{}.out".format(self.file_copy_output, num, self.src_md5sum[-4:])
                cp_pid = host_handle.start_bg_process(command=cp_cmd, output_file=cp_file_output)
                fun_test.log("File copy is started in background, pid is: {}".format(cp_pid))

            fun_test.sleep(message="Sleeping for {} seconds before before bringing up the failed device(s) & "
                                   "plex rebuild".format(wait_time), seconds=wait_time)
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                fail_uuid = self.ec_info["uuids"][num]["blt"][
                    self.failure_drive_index[num - self.test_volume_start_index]]
                fail_device = self.ec_info["device_id"][num][
                    self.failure_drive_index[num - self.test_volume_start_index]]

                if not self.rebuild_on_spare_volume:
                    if self.fail_drive:
                        ''' Marking drive as online '''
                        device_up_status = self.storage_controller.enable_device(device_id=fail_device,
                                                                                 command_duration=self.command_timeout)
                        fun_test.test_assert(device_up_status["status"], "Enabling Device ID {}".format(fail_device))

                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                        fun_test.test_assert_expected(expected="DEV_ONLINE",
                                                      actual=device_stats["data"]["device state"],
                                                      message="Device ID {} is Enabled again".format(fail_device))
                        ''' Marking drive as online '''
                    else:
                        ''' Marking Plex as online '''
                        volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                        fun_test.test_assert(volume_fail_status["status"], "Re-enabling Volume UUID {}".
                                             format(fail_uuid))
                        # Validate if Volume is enabled again
                        device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                                 fail_uuid)
                        volume_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.test_assert_expected(expected=0,
                                                      actual=volume_stats["data"]["stats"]["fault_injection"],
                                                      message="Plex is marked as online")
                        ''' Marking Plex as online '''

                # Rebuild failed plex
                if self.rebuild_on_spare_volume:
                    spare_uuid = self.spare_vol_uuid
                    fun_test.log("Rebuilding on spare volume: {}".format(spare_uuid))
                else:
                    spare_uuid = fail_uuid
                    fun_test.log("Rebuilding on failed volume: {}".format(spare_uuid))
                rebuild_device = self.storage_controller.plex_rebuild(
                    subcmd="ISSUE", type=self.ec_info["volume_types"]["ec"],
                    uuid=self.ec_info["uuids"][num]["ec"][num - self.test_volume_start_index],
                    failed_uuid=fail_uuid, spare_uuid=spare_uuid, rate=self.rebuild_rate)
                fun_test.test_assert(rebuild_device["status"], "Rebuild failed Plex {}".format(fail_uuid))
                fun_test.log("Rebuild failed Plex {} status {}".format(fail_uuid, rebuild_device["status"]))

            timer = FunTimer(max_time=cp_timeout)
            while not timer.is_expired():
                fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
                output = host_handle.get_process_id_by_pattern(process_pat=cp_pid, multiple=True)
                if not output:
                    fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file2))
                    break
            else:
                fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file2))

            # Parsing copy time output and recording time taken to copy file
            read_output = host_handle.read_file(file_name=cp_file_output)
            lines = read_output.split("\n")
            result = {}
            for num, line in enumerate(lines):
                search_time = re.search(r'(\d+)', line)
                if search_time:
                    if re.search("([0-9].*)", search_time.group(1)):
                        result[num] = search_time.group(1)
            fun_test.log("Recorded start time: {} and end time: {} for file copy".format(result[0], result[1]))
            file_copy_time_during_rebuild = int(result[1]) - int(result[0])
            fun_test.log("Time to copy the file during volume rebuild: {} sec".format(file_copy_time_during_rebuild))
            host_handle.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)

            row_data_dict["copy_time_during_rebuild"] = file_copy_time_during_rebuild
            row_data_dict["fio_job_name"] = "inspur_functional_8_7_1_f1_{}_vol_{}_host_{}".format(
                self.num_f1s, self.ec_info["num_volumes"], self.num_hosts)
            row_data_dict["vol_size"] = str(self.ec_info["capacity"] / (1024 ** 3)) + "G"
            row_data_dict["test_file_size"] = str(self.test_file_size / (1024 ** 3)) + "G"

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

            self.host_info[host_name]["dst_file"]["file2"] = {}
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                if num not in self.host_info[host_name]["dst_file"]["file2"]:
                    self.host_info[host_name]["dst_file"]["file2"][num] = {}
                    self.host_info[host_name]["dst_file"]["file2"][num]["md5sum"] = []
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
                self.host_info[host_name]["dst_file"]["file2"][num]["md5sum"].append(self.dst_md5sum)

            # Re-verifying integrity of file1 after rebuild successful
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                cur_dst_file = dst_file1[num - self.test_volume_start_index]
                dst_file_info = host_handle.ls(cur_dst_file)
                fun_test.simple_assert(dst_file_info, "Copied file {} exists".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.test_file_size, actual=dst_file_info["size"],
                                              message="Copying {} bytes file into {}".format(self.test_file_size,
                                                                                             cur_dst_file))
                self.dst_md5sum = host_handle.md5sum(file_name=cur_dst_file, timeout=cp_timeout)
                fun_test.test_assert(self.dst_md5sum, "Finding md5sum of existing file {}".format(cur_dst_file))
                fun_test.test_assert_expected(expected=self.host_info[host_name]["src_file"]["file1"]["md5sum"][0],
                                              actual=self.dst_md5sum,
                                              message="Comparing md5sum of source & existing file before rebuild")
            ''' finish: File copy while the BLT volume is rebuilding '''

            # Parsing f1 uart log file to search rebuild start and finish time
            '''
            log file output:
            [2537.762236 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 under rebuild total failed:1"
            [2774.291395 2.2.3] ALERT ecvol "storage/flvm/ecvol/ecvol.c:3312:ecvol_rebuild_done_process_push() Rebuild operation complete for plex:5"
            [2774.292149 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 marked active total failed:0"
            '''
            try:
                bmc_handle = self.fs_obj[0].get_bmc()
                uart_log_file = self.fs_obj[0].get_bmc().get_f1_uart_log_filename(f1_index=self.f1_in_use)
                fun_test.log("F1 UART Log file used to check Rebuild operation status: {}".format(uart_log_file))
                search_pattern = "'under rebuild total failed'"
                output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                                   timeout=self.command_timeout))
                fun_test.test_assert_expected(expected=1, actual=int(output.rstrip()),
                                              message="Rebuild operation is started")
                rebuild_start_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".format(
                    search_pattern, uart_log_file, timeout=self.command_timeout))
                rebuild_start_time = int(round(float(rebuild_start_time.rstrip())))
                fun_test.log("Rebuild operation started at : {}".format(rebuild_start_time))

                timer = FunTimer(max_time=self.rebuild_timeout)
                while not timer.is_expired():
                    search_pattern = "'Rebuild operation complete for plex'"
                    fun_test.sleep("Waiting for plex rebuild to complete", seconds=(self.status_interval * 5))
                    output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                                       timeout=self.command_timeout))
                    if int(output.rstrip()) == 1:
                        rebuild_stop_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".
                            format(search_pattern, uart_log_file, timeout=self.command_timeout))
                        rebuild_stop_time = int(round(float(rebuild_stop_time.rstrip())))
                        fun_test.log("Rebuild operation completed at: {}".format(rebuild_stop_time))
                        fun_test.log("Rebuild operation on plex {} is completed".format(spare_uuid))
                        break
                else:
                    fun_test.test_assert(False, "Rebuild operation on plex {} completed".format(spare_uuid))
                plex_rebuild_time = rebuild_stop_time - rebuild_start_time
                fun_test.log("Time taken to rebuild plex: {}".format(plex_rebuild_time))
                row_data_dict["plex_rebuild_time"] = plex_rebuild_time
            except Exception as ex:
                fun_test.critical(str(ex))

            # Building the table raw for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Single Drive Failure Result Table", table_name=self.summary,
                               table_data=table_data)

            # Datetime required for daily Dashboard data filter
            try:
                # Building value_dict for dashboard update
                value_dict = {
                    "date_time": self.db_log_time,
                    "platform": FunPlatform.F1,
                    "version": fun_test.get_version(),
                    "num_hosts": self.num_hosts,
                    "num_f1s": self.num_f1s,
                    "base_file_copy_time": base_file_copy_time,
                    "copy_time_during_plex_fail": copy_time_during_plex_fail,
                    "file_copy_time_during_rebuild": file_copy_time_during_rebuild,
                    "plex_rebuild_time": plex_rebuild_time
                }
                if self.post_results:
                    fun_test.log("Posting results on dashboard")
                    add_to_data_base(value_dict)
                    # post_results("Inspur Performance Test", test_method, *row_data_list)
            except Exception as ex:
                fun_test.critical(str(ex))

            try:
                if hasattr(self, "back_pressure") and self.back_pressure:
                    # Check if back pressure is still running, if yes, stop it
                    check_pid = host_handle.get_process_id(process_name="fio")
                    if check_pid:
                        fun_test.log("Back pressure is still running, stopping it")
                        host_handle.pkill(process_name="fio")
                        # fun_test.test_assert_expected(expected=0, actual=host_handle.exit_status(),
                        #                               message="Back pressure is stopped")
                        fun_test.log("Back pressure is stopped")
            except Exception as ex:
                fun_test.critical(str(ex))
        """

    def cleanup(self):
        pass


class DurVolDataReconWithBP(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Durable Volume: EC: Data Reconstruction Cases",
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
        super(DurVolDataReconWithBP, self).setup()

    def run(self):
        super(DurVolDataReconWithBP, self).run()

    def cleanup(self):
        super(DurVolDataReconWithBP, self).cleanup()


if __name__ == "__main__":
    ecscript = DurableVolScript()
    ecscript.add_test_case(DurVolDataReconWithBP())
    ecscript.run()
