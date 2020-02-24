from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from lib.system.utils import *
from lib.host.storage_controller import *
from collections import OrderedDict, Counter
from math import ceil
from lib.templates.storage.storage_controller_api import *


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


class StripeVolDiskFailTestScript(FunTestScript):
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
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = False
        fun_test.test_assert(expression=self.num_hosts >= 2, message="Test bed has minimum hosts (3) required")

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
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info

        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            # # Ensure all hosts are up after reboot
            # fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
            #                      message="Ensure Host {} is reachable after reboot".format(host_name))
            #
            # # Ensure required modules are loaded on host server, if not load it
            # for module in self.load_modules:
            #     module_check = host_handle.lsmod(module)
            #     if not module_check:
            #         host_handle.modprobe(module)
            #         module_check = host_handle.lsmod(module)
            #         fun_test.sleep("Loading {} module".format(module))
            #     fun_test.simple_assert(module_check, "{} module is loaded".format(module))

            # Stopping iptables service on all hosts
            host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
            host_handle.sudo_command("systemctl stop irqbalance")
            irq_bal_stat = host_handle.command("systemctl status irqbalance")
            if "dead" in irq_bal_stat:
                fun_test.log("IRQ balance stopped on host: {}".format(host_name))
            else:
                fun_test.log("IRQ balance not stopped on host: {}".format(host_name))
                host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

        # # Ensuring connectivity from Host to F1's
        # for host_name in self.host_info:
        #     host_handle = self.host_info[host_name]["handle"]
        #     for index, ip in enumerate(self.f1_ips):
        #         ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
        #         fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
        #                              format(host_name, self.funcp_spec[0]["container_names"][index], ip))

    def cleanup(self):
        pass


class StripeVolDiskFailTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict[testcase].items():
            setattr(self, k, v)

        fun_test.log("Config Config: {}".format(self.__dict__))

        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

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
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        fun_test.shared_variables["transport_type"] = self.transport_type

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["nvme_connect"] = False
            fun_test.shared_variables["blt"]["warmup_io_completed"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # Compute the individual BLT sizes
            self.capacity = int(
                ceil(self.stripe_details["vol_size"] / (self.blt_count * self.blt_details["block_size"]))
                * self.blt_details["block_size"]
            )

            # Create BLTs for striped volume
            self.stripe_unit_size = self.stripe_details["block_size"] * self.stripe_details["stripe_unit"]
            self.blt_capacity = self.stripe_unit_size + self.capacity
            if (self.blt_capacity / self.stripe_unit_size) % 2:
                fun_test.log("Num of block in BLT is not even")
                self.blt_capacity += self.stripe_unit_size

            self.thin_uuid = []
            for i in range(1, self.blt_count + 1, 1):
                cur_uuid = generate_uuid()
                self.thin_uuid.append(cur_uuid)
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_capacity,
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i, cur_uuid))
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid

            self.strip_vol_size = (self.blt_capacity - self.stripe_unit_size) * self.blt_count
            # Create Strip Volume
            self.stripe_uuid = generate_uuid()
            command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                                   capacity=self.strip_vol_size,
                                                                   name="stripevol1",
                                                                   uuid=self.stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))

            # Create TCP controllers for first host
            self.ctrlr_uuid = []
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    self.ctrlr_uuid.append(utils.generate_uuid())
                    command_result = self.storage_controller.create_controller(ctrlr_id=index,
                                                                               ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                               ctrlr_type="BLOCK",
                                                                               transport=self.transport_type.upper(),
                                                                               remote_ip=
                                                                               self.host_info[host_name]["ip"],
                                                                               subsys_nqn=self.nvme_subsystem,
                                                                               host_nqn=
                                                                               self.host_info[host_name]["ip"],
                                                                               port=self.transport_port,
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Create Storage Controller for {} with controller uuid {} on DUT for host {}".
                                         format(self.transport_type.upper(), self.ctrlr_uuid[-1], host_name))

                    # Attaching volume to NVMeOF controller
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[index],
                        ns_id=self.stripe_details["ns_id"],
                        vol_uuid=self.stripe_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Attach NVMeOF controller {} to stripe vol {} over {} for host {}".
                                         format(self.ctrlr_uuid[index], self.stripe_uuid,
                                                self.transport_type.upper(), host_name))

            # Starting packet capture in all the hosts
            self.pcap_started = {}
            self.pcap_stopped = {}
            self.pcap_pid = {}
            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    test_interface = self.host_info[host_name]["test_interface"].name
                    self.pcap_started[host_name] = False
                    self.pcap_stopped[host_name] = True
                    self.pcap_pid[host_name] = {}
                    self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                        interface=test_interface, tcpdump_filename="/tmp/nvme_connect.pcap", snaplen=1500)
                    if self.pcap_pid[host_name]:
                        fun_test.log("Started packet capture in {}".format(host_name))
                        self.pcap_started[host_name] = True
                        self.pcap_stopped[host_name] = False
                    else:
                        fun_test.critical("Unable to start packet capture in {}".format(host_name))

                    if not fun_test.shared_variables["blt"]["nvme_connect"]:
                        # Checking nvme-connect status
                        if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                nvme_io_queues=self.nvme_io_queues,
                                hostnqn=self.host_info[host_name]["ip"])
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                hostnqn=self.host_info[host_name]["ip"])

                        if self.pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                            self.pcap_stopped[host_name] = True

                        fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                        lsblk_output = host_handle.lsblk("-b")
                        fun_test.simple_assert(lsblk_output, "Listing available volumes")

                        self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                        host_handle.sudo_command("dmesg")
                        lsblk_output = host_handle.lsblk()
                        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".
                                             format(self.volume_name))
                        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                                      message="{} device type check".format(self.volume_name))

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))
            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

            before_write_eqm = {}
            after_write_eqm = {}
            before_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for index, host_name in enumerate(self.host_info):
                if index == 0:
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]

                    # Create filesystem if needed else write to raw device
                    if hasattr(self, "create_file_system") and self.create_file_system:
                        host_handle.sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
                        host_handle.sudo_command("mount {} /mnt".format(self.nvme_block_device))
                        fun_test.log("Creating a testfile on XFS volume")
                        fio_output = host_handle.pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
                        host_handle.sudo_command("umount /mnt")
                        # Mount NVMe disk on host in Read-Only mode if on a filesystem
                        host_handle.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
                    else:
                        fio_output = host_handle.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Writing the entire volume")
                    fun_test.shared_variables["blt"]["warmup_io_completed"] = True
                    # host_handle.disconnect()

            after_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in before_write_eqm["data"]["eqm_stats"].items():
                current_value = after_write_eqm["data"]["eqm_stats"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    stats_delta = current_value - value
                    fun_test.log("Write test : there is a mismatch in {} : {}".format(field, stats_delta))

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):
        testcase = self.__class__.__name__

        # Test Preparation
        # Checking whether the ec_info is having the drive and device ID for the EC's plex volumes
        # Else going to extract the same

        self.stripe_info = {}
        fun_test.log("Pulling information of Drive and Device ID of the BLT volumes of stripe volume")
        self.stripe_info["drive_uuid"] = []
        self.stripe_info["device_id"] = []
        for num in xrange(self.blt_count):
            blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", self.thin_uuid[num],
                                                     "stats")
            blt_stats = self.storage_controller.peek(blt_props_tree)
            fun_test.simple_assert(blt_stats["status"], "Stats of BLT Volume {}".format(self.thin_uuid[num]))
            if "drive_uuid" in blt_stats["data"]:
                self.stripe_info["drive_uuid"].append(blt_stats["data"]["drive_uuid"])
            else:
                fun_test.simple_assert(blt_stats["data"].get("drive_uuid"), "Drive UUID of BLT volume {}".
                                       format(self.thin_uuid[num]))
            drive_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                       "drives", blt_stats["data"]["drive_uuid"])
            drive_stats = self.storage_controller.peek(drive_props_tree)
            fun_test.simple_assert(drive_stats["status"], "Stats of the drive {}".
                                   format(blt_stats["data"]["drive_uuid"]))
            if "drive_id" in drive_stats["data"]:
                self.stripe_info["device_id"].append(drive_stats["data"]["drive_id"])
            else:
                fun_test.simple_assert(drive_stats["data"].get("drive_id"), "Device ID of the drive {}".
                                       format(blt_stats["data"]["drive_uuid"]))

        fun_test.log("BLT volumes UUID      : {}".format(self.thin_uuid))
        fun_test.log("BLT volumes drive UUID: {}".format(self.stripe_info["drive_uuid"]))
        fun_test.log("BLT volumes device ID : {}".format(self.stripe_info["device_id"]))

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}

        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = self.nvme_block_device
        # volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])

        fio_size = int(divide(n=100, d=(self.num_hosts - 1)))
        self.fio_cmd_args1["size"] = "{}{}".format(str(fio_size), "%")

        fio_offset_diff = fio_size

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}

            test_thread_id = {}
            host_clone = {}

            for index, host_name in enumerate(self.host_info):
                if index != 0:
                    fun_test.sleep("add host at interval of {}".format(self.add_host_delay), self.add_host_delay)
                    # Create NVMe-OF controller for rest of hosts
                    self.ctrlr_uuid.append(utils.generate_uuid())
                    command_result = self.storage_controller.create_controller(
                        ctrlr_id=index, ctrlr_uuid=self.ctrlr_uuid[-1], ctrlr_type="BLOCK",
                        transport=self.transport_type.upper(), remote_ip=self.host_info[host_name]["ip"],
                        subsys_nqn=self.nvme_subsystem, host_nqn=self.host_info[host_name]["ip"],
                        port=self.transport_port, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Create Storage Controller for {} with controller uuid {} on DUT for host {}".
                                         format(self.transport_type.upper(), self.ctrlr_uuid[-1], host_name))

                    # Attach volume to NVMe-OF controller
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[-1], ns_id=self.stripe_details["ns_id"],
                        vol_uuid=self.stripe_uuid, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Attach NVMeOF controller {} to stripe vol {} over {} for host {}".
                                         format(self.ctrlr_uuid[-1], self.stripe_uuid, self.transport_type.upper(),
                                                host_name))

                    # NVMe connect
                    fun_test.shared_variables["blt"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    test_interface = self.host_info[host_name]["test_interface"].name
                    self.pcap_started[host_name] = False
                    self.pcap_stopped[host_name] = True
                    self.pcap_pid[host_name] = {}
                    self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                        interface=test_interface, tcpdump_filename="/tmp/nvme_connect.pcap", snaplen=1500)
                    if self.pcap_pid[host_name]:
                        fun_test.log("Started packet capture in {}".format(host_name))
                        self.pcap_started[host_name] = True
                        self.pcap_stopped[host_name] = False
                    else:
                        fun_test.critical("Unable to start packet capture in {}".format(host_name))

                    if not fun_test.shared_variables["blt"]["nvme_connect"]:
                        # Checking nvme-connect status
                        if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                nvme_io_queues=self.nvme_io_queues,
                                hostnqn=self.host_info[host_name]["ip"])
                        else:
                            nvme_connect_status = host_handle.nvme_connect(
                                target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                                port=self.transport_port, transport=self.transport_type.lower(),
                                hostnqn=self.host_info[host_name]["ip"])

                        if self.pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                            self.pcap_stopped[host_name] = True

                        fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                        lsblk_output = host_handle.lsblk("-b")
                        fun_test.simple_assert(lsblk_output, "Listing available volumes")

                        host_handle.sudo_command("dmesg")
                        lsblk_output = host_handle.lsblk()
                        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".
                                             format(self.volume_name))
                        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                                      message="{} device type check".format(self.volume_name))

                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                if index == 0:
                    # Starting Read for whole volume on first host
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args)
                else:
                    # Starting IO on rest of hosts for particular LBA range
                    self.fio_cmd_args1["offset"] = "{}{}".format(str((index - 1) * fio_offset_diff), "%")
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args1)

            fun_test.log("\n\n********** Injecting failure in volume / drive **********\n\n")
            # Check whether the drive failure needs to be triggered
            if hasattr(self, "trigger_failure") and self.trigger_failure:
                # Sleep for sometime before triggering the drive failure
                fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".
                               format(self.trigger_failure_delay), seconds=self.trigger_failure_delay)
                # Check whether the drive index to be failed is given or not. If not pick a random one
                if self.failure_mode == "random" or not hasattr(self, "failure_drive_index"):
                    self.failure_drive_index = []
                    for num in xrange(self.blt_count):
                        self.failure_drive_index.append(random.randint(0, self.blt_count - 1))
                fail_uuid = self.thin_uuid[self.failure_drive_index[0]]
                fail_device = self.stripe_info["device_id"][self.failure_drive_index[0]]

                # Triggering the drive failure
                if self.fail_drive:
                    ''' Marking drive as failed '''
                    # Inducing failure in drive
                    fun_test.log("Device to be marked as fail: {}".format(fail_device))
                    fun_test.log("Initiating drive failure")
                    device_fail_status = self.storage_controller.disable_device(device_id=fail_device,
                                                                                command_duration=self.command_timeout)
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
                    ''' Marking Volume as failed '''
                    # Inducing failure in one of the Plex of the volume
                    fun_test.log("uuid to be marked as fail: {}".format(fail_uuid))
                    fun_test.log("Initiating BLT failure")
                    volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                    fun_test.test_assert(volume_fail_status["status"], "Disabling BLT UUID {}".format(fail_uuid))
                    # Validate if volume is marked as Failed
                    device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", fail_uuid)
                    volume_stats = self.storage_controller.peek(device_props_tree)
                    fun_test.test_assert_expected(expected=1, actual=volume_stats["data"]["stats"]["fault_injection"],
                                                  message="Volume is marked as Failed")
                    ''' Marking Volume as failed '''

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
                self.storage_controller.verbose = True

            try:
                fun_test.log("Trying Write only operation on fault injected disk")
                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    if index == 0:
                        fio_output = host_handle.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                        fun_test.log("Write on fault injected disk: {}".format(fio_output))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Expected Write IO failure on index: {}, host {}".format(index, host_name))

            try:
                fun_test.log("Trying Read only operation on fault injected disk")
                self.fio_cmd_args["rw"] = "read"
                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    if index == 0:
                        fio_output = host_handle.pcie_fio(filename=self.nvme_block_device, **self.fio_cmd_args)
                        fun_test.log("Reading the entire volume: {}".format(fio_output))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Expected Read FIO failure on index: {}, host {}".format(index, host_name))

            fun_test.sleep("Waiting in between iterations", self.iter_interval)

        # NVMe-disconnect so next volume can be attached to host
        try:
            for index, host_name in enumerate(self.host_info):
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)  # TODO: SWOS-6165
                # nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)

                # Skipping disconnect from host4 as it's already disconnected
                host_handle = self.host_info[host_name]["handle"]
                host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="{} - NVME Disconnect Status".format(host_name))

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes on nvme-disconnect")
        except Exception as ex:
            fun_test.critical(str(ex))

        # Creating second volume and moving hosts to new volume
        self.thin_uuid2 = []
        for i in range(0, self.blt_count):
            cur_uuid = generate_uuid()
            self.thin_uuid2.append(cur_uuid)
            command_result = self.storage_controller.create_thin_block_volume(
                capacity=self.blt_capacity,
                block_size=self.blt_details["block_size"],
                name="thin_block2" + str(i + 1),
                uuid=cur_uuid,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i, cur_uuid))
        fun_test.shared_variables["thin_uuid2"] = self.thin_uuid2

        # Create Strip Volume
        self.stripe_uuid2 = generate_uuid()
        command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                               capacity=self.strip_vol_size,
                                                               name="stripevol2",
                                                               uuid=self.stripe_uuid2,
                                                               block_size=self.stripe_details["block_size"],
                                                               stripe_unit=self.stripe_details["stripe_unit"],
                                                               pvol_id=self.thin_uuid2,
                                                               command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                             format(self.stripe_uuid2))

        ns_id2 = int(self.stripe_details["ns_id"]) + 1
        self.nvme_block_device2 = self.nvme_device + "n" + str(ns_id2)

        # Attaching second volume to NVMeOF controller
        for index, host_name in enumerate(self.host_info):
            command_result = self.storage_controller.attach_volume_to_controller(
                ctrlr_uuid=self.ctrlr_uuid[index],
                ns_id=ns_id2,
                vol_uuid=self.stripe_uuid2,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Attach NVMeOF controller {} to stripe vol {} over {} for host {}".
                                 format(self.ctrlr_uuid[index], self.stripe_uuid2, self.transport_type.upper(),
                                        host_name))

        fun_test.shared_variables["blt2"] = {}
        fun_test.shared_variables["blt2"]["setup_created"] = False
        fun_test.shared_variables["blt2"]["nvme_connect"] = False
        fun_test.shared_variables["blt2"]["warmup_io_completed"] = False

        # Starting packet capture in all the hosts
        self.pcap_started = {}
        self.pcap_stopped = {}
        self.pcap_pid = {}
        for index, host_name in enumerate(self.host_info):
            fun_test.shared_variables["blt2"][host_name] = {}
            host_handle = self.host_info[host_name]["handle"]
            test_interface = self.host_info[host_name]["test_interface"].name
            self.pcap_started[host_name] = False
            self.pcap_stopped[host_name] = True
            self.pcap_pid[host_name] = {}
            self.pcap_pid[host_name] = host_handle.tcpdump_capture_start(
                interface=test_interface, tcpdump_filename="/tmp/nvme_connect_2.pcap", snaplen=1500)
            if self.pcap_pid[host_name]:
                fun_test.log("Started packet capture in {}".format(host_name))
                self.pcap_started[host_name] = True
                self.pcap_stopped[host_name] = False
            else:
                fun_test.critical("Unable to start packet capture in {}".format(host_name))

            if not fun_test.shared_variables["blt2"]["nvme_connect"]:
                # Checking nvme-connect status
                if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                    nvme_connect_status = host_handle.nvme_connect(
                        target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                        port=self.transport_port, transport=self.transport_type.lower(),
                        nvme_io_queues=self.nvme_io_queues,
                        hostnqn=self.host_info[host_name]["ip"])
                else:
                    nvme_connect_status = host_handle.nvme_connect(
                        target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                        port=self.transport_port, transport=self.transport_type.lower(),
                        hostnqn=self.host_info[host_name]["ip"])

                if self.pcap_started[host_name]:
                    host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[host_name])
                    self.pcap_stopped[host_name] = True

                fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")

                self.volume_name2 = self.nvme_device.replace("/dev/", "") + "n" + str(ns_id2)
                host_handle.sudo_command("dmesg")
                lsblk_output = host_handle.lsblk()
                fun_test.test_assert(self.volume_name2 in lsblk_output, "{} device available".
                                     format(self.volume_name2))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name2]["type"],
                                              message="{} device type check".format(self.volume_name2))

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}
        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename2 = "/mnt/testfile.dat"
        else:
            test_filename2 = self.nvme_block_device2

        fio_size = int(divide(n=100, d=(self.num_hosts - 1)))
        self.fio_cmd_args1["size"] = "{}{}".format(str(fio_size), "%")
        fio_offset_diff = fio_size

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}

            test_thread_id = {}
            host_clone = {}

            for index, host_name in enumerate(self.host_info):
                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                if index == 0:
                    # Create filesystem if needed else write to raw device
                    if hasattr(self, "create_file_system") and self.create_file_system:
                        host_handle.sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device2))
                        host_handle.sudo_command("mount {} /mnt".format(self.nvme_block_device2))
                        fun_test.log("Creating a testfile on XFS volume")
                        fio_output = host_handle.pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
                        host_handle.sudo_command("umount /mnt")
                        # Mount NVMe disk on host in Read-Only mode if on a filesystem
                        host_handle.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device2))
                    else:
                        fio_output = host_handle.pcie_fio(filename=self.nvme_block_device2, **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Writing the entire volume")
                    fun_test.shared_variables["blt"]["warmup_io_completed"] = True

                    # Starting Read for whole volume on first host
                    self.fio_cmd_args["rw"] = "randread"
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename2,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args)
                else:
                    # Starting IO on rest of hosts for particular LBA range
                    self.fio_cmd_args1["offset"] = "{}{}".format(str((index - 1) * fio_offset_diff), "%")
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename=test_filename2,
                                                                          iodepth=iodepth,
                                                                          name="fio_{}".format(host_name),
                                                                          **self.fio_cmd_args1)
            # Waiting for all the FIO test threads to complete
            try:
                fun_test.sleep("for threads to start", 10)
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
                self.storage_controller.verbose = True

            for index, host_name in enumerate(self.host_info):
                fun_test.log(fun_test.shared_variables["fio"][index], "FIO test with on {}".format(host_name))

    def cleanup(self):
        # Volume un-configuration
        try:
            fun_test.log("\n\n********** Deleting volume **********\n\n")
            for index, host_name in enumerate(self.host_info):
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)  # TODO: SWOS-6165
                # nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)

                # Skipping disconnect from host4 as it's already disconnected
                host_handle = self.host_info[host_name]["handle"]
                host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="{} - NVME Disconnect Status".format(host_name))

                # Detach volume from NVMe-OF controller
                command_result = self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=self.ctrlr_uuid[index], ns_id=self.stripe_details["ns_id"],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "{} - Detach NVMeOF controller {}".format(
                    host_name, self.ctrlr_uuid[index]))
        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            # Delete Strip Volume
            command_result = self.storage_controller.delete_volume(type=self.stripe_details["type"],
                                                                   capacity=self.strip_vol_size,
                                                                   name="stripevol1",
                                                                   uuid=self.stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))
        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            for i in range(self.blt_count):
                command_result = self.storage_controller.delete_thin_block_volume(
                    capacity=self.blt_capacity,
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i+1),
                    uuid=self.thin_uuid[i],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(i, self.thin_uuid[i]))
        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                for filename in ["/tmp/nvme_connect.pcap", "/tmp/nvme_connect_2.pcap"]:
                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path=filename, target_file_path=pcap_artifact_file)
                fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                            filename=pcap_artifact_file)
        except Exception as ex:
            fun_test.critical(str(ex))


class StripedVolDiskFailRecovery(StripeVolDiskFailTestCase):
    def describe(self):
        self.set_test_details(
            id=1,
            summary="Verifying drive failure and recovery with new Stripe Volume",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host and perform sequential write
                3. Start Random Read on whole volume from first host
                4. Start Random Read-Write with data integrity from rest of the volumes
                5. Inject failure in one of the drive where BLT is created
                6. Verify impact on IO
                7. Create another stripe volume and attach it to hosts
                8. Initiate IO again
                ''')

    def setup(self):
        super(StripedVolDiskFailRecovery, self).setup()

    def run(self):
        super(StripedVolDiskFailRecovery, self).run()

    def cleanup(self):
        super(StripedVolDiskFailRecovery, self).cleanup()


if __name__ == "__main__":
    testscript = StripeVolDiskFailTestScript()
    testscript.add_test_case(StripedVolDiskFailRecovery())
    testscript.run()
