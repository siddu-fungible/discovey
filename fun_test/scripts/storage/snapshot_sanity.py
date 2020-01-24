from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.storage.storage_controller_api import *
import random


# Get NVMe device details
def get_nvme_device(host_obj):
    nvme_list_raw = host_obj.sudo_command("nvme list -o json")
    host_obj.disconnect()
    if str(nvme_list_raw) in "":
        fio_filename = None
    elif "failed to open" in nvme_list_raw.lower():
        nvme_list_raw = nvme_list_raw + "}"
        temp1 = nvme_list_raw.replace('\n', '')
        temp2 = re.search(r'{.*', temp1).group()
        nvme_list_dict = json.loads(temp2, strict=False)
    else:
        try:
            nvme_list_dict = json.loads(nvme_list_raw)
        except:
            nvme_list_raw = nvme_list_raw + "}"
            nvme_list_dict = json.loads(nvme_list_raw, strict=False)

    try:
        nvme_device_list = []
        for device in nvme_list_dict["Devices"]:
            if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"] or \
                    "fs1600" in device["ModelNumber"].lower():
                nvme_device_list.append(device["DevicePath"])
            elif "unknown device" in device["ProductName"].lower() or "null" in device["ProductName"].lower():
                if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
                    nvme_device_list.append(device["DevicePath"])
        fio_filename = str(':'.join(nvme_device_list))
    except:
        fio_filename = None

    return fio_filename


def fio_parser(arg1, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"] = fio_output
    fun_test.simple_assert(fio_output, "Fio result")
    arg1.disconnect()


class Singledpu(FunTestScript):
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
        fun_test.shared_variables["ctrl_created"] = False

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
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = False

        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")

        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6
                if self.syslog != "default":
                    command_result = self.storage_controller.poke("params/syslog/level 6")
                    fun_test.test_assert(command_result["status"], "Setting syslog level to 6")

                    command_result = self.storage_controller.peek("params/syslog/level")
                    fun_test.test_assert_expected(expected=6, actual=command_result["data"],
                                                  message="Checking syslog level set to 6")

                # Executing NVMe disconnect from all the hosts
                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")


class SnapVolumeTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        benchmark_parsing = True
        testcase_file = ""
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))

        testcase_dict = {}
        testcase_dict = utils.parse_file_to_json(testcase_file)

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
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
        self.end_host = self.host_handles[self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        self.linux_host_inst = {}

        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")
        # Configuring controller
        if not fun_test.shared_variables["ctrl_created"]:
            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"],
                                                            port=self.transport_port)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")
            fun_test.shared_variables["ctrl_created"] = True

        self.final_host_ips = self.host_ips[:]

        self.thin_uuid = 0
        self.cow_uuid = {}
        self.snap_uuid = {}
        self.block_size = {}
        self.vol_capacity = {}
        self.nvme_block_device = []
        self.ctrlr_uuid = []
        self.nqn_list = []
        self.bv_attach = False

        if not hasattr(self, "snap_attach"):
            self.snap_attach = False

        self.ctrlr_uuid = utils.generate_uuid()
        nqn = "nqn"
        self.nqn_list.append(nqn)
        command_result = self.storage_controller.create_controller(ctrlr_id=1,
                                                                   ctrlr_uuid=self.ctrlr_uuid,
                                                                   ctrlr_type="BLOCK",
                                                                   transport=self.transport_type.upper(),
                                                                   remote_ip=self.remote_ip,
                                                                   subsys_nqn=nqn,
                                                                   host_nqn=self.remote_ip,
                                                                   port=self.transport_port,
                                                                   command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Creating TCP controller for {}".
                             format(self.remote_ip))

        # Create Base volume
        self.thin_uuid = utils.generate_uuid()
        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="thin_block_1",
                                                               uuid=self.thin_uuid,
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Creation of base volume")

        # Check if BV is there
        # command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/{}".
        #                                               format(self.thin_uuid))

        # Attach Base volume to controller before creating SNAP volume
        if not self.bv_attach:
            if hasattr(self, "attach_basevol") and self.attach_basevol:
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     vol_uuid=self.thin_uuid,
                                                                                     ns_id=1,
                                                                                     command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Attach base volume to controller")
                self.bv_attach = True

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    fun_test.shared_variables["host_handle"] = host_handle
                    host_ip = self.host_info[host_name]["ip"]
                    nqn = self.nqn_list[index]
                    # Stop udev services on host
                    service_list = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
                    for service in service_list:
                        service_status = host_handle.systemctl(service_name=service, action="stop")
                        fun_test.simple_assert(service_status, "Stopping {} service on {}".format(service,
                                                                                                  self.host_info[host_name]))
                    host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                    host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                    if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                        command_result = host_handle.sudo_command(
                            "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                                      self.test_network["f1_loopback_ip"],
                                                                                      self.transport_port, nqn,
                                                                                      self.nvme_io_queues, host_ip))
                        fun_test.log(command_result)
                    else:
                        command_result = host_handle.sudo_command(
                            "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                                self.test_network["f1_loopback_ip"],
                                                                                self.transport_port, nqn, host_ip))
                        fun_test.log(command_result)
                    fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                    host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                    host_handle.sudo_command("dmesg")
                    fun_test.shared_variables["host_handle"] = host_handle
                    self.device_details = get_nvme_device(host_handle)
                    host_handle.disconnect()
                    if not self.device_details:
                        host_handle.command("dmesg")
                        fun_test.shared_variables["nvme_discovery"] = False
                        fun_test.simple_assert(False, "NVMe device not found")
                    else:
                        fun_test.shared_variables["nvme_discovery"] = True

        # Create SNAP
        for x in range(1, self.snap_count + 1, 1):
            self.cow_uuid[x] = utils.generate_uuid()
            self.snap_uuid[x] = utils.generate_uuid()

            # Create COW volume
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="cow_vol_" + str(x),
                                                                   uuid=self.cow_uuid[x],
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Creation of COW volume")

            # Create SNAP vol
            if hasattr(self, "skip_fio") and self.skip_fio:
                # Snapvolume just contains bitmap so calculate the size required based on BV size
                # Num of blocks
                num_blocks = self.blt_details["capacity"] / self.blt_details["block_size"]
                self.snap_capacity = num_blocks
                command_result = self.storage_controller.create_snap_volume(
                    capacity=self.snap_capacity,
                    block_size=self.blt_details["block_size"],
                    name="snap_vol_" + str(x),
                    uuid=self.snap_uuid[x],
                    cow_uuid=self.cow_uuid[x],
                    base_uuid=self.thin_uuid,
                    command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Creation of Snap Volume")
                fun_test.sleep("Snap vol created")

                if self.snap_attach:
                    # Attach snapvolume to controller
                    command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                         vol_uuid=self.snap_uuid[x],
                                                                                         ns_id=x + 1,
                                                                                         command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Attach Snap Volume to controller".
                                         format(self.snap_uuid[x], self.ctrlr_uuid))

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[3:]

        self.linux_host = fun_test.shared_variables["host_handle"]
        snap_vol_created = False
        check_test_mode = []

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_output = {}
        diff_volume_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}

        self.storage_controller.peek("storage")

        for combo in self.fio_bs_iodepth:
            fio_output[combo] = {}
            final_volume_stats[combo] = {}
            diff_volume_stats[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            for mode in self.fio_modes:
                if mode in check_test_mode and mode == "write":
                    self.fio_cmd_args["verify_pattern"] = "\\\"DEADCAFE\\\""
                else:
                    if mode not in check_test_mode:
                        check_test_mode.append(mode)
                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Get base & COW volume stats before fio
                initial_cow_vol_stats = {}
                initial_base_vol_stats = None
                initial_base_vol_stats = self.storage_controller.peek("storage/volume/VOL_TYPE_BLK_LOCAL_THIN/{}".
                                                                      format(self.thin_uuid))
                for x in range(1, self.snap_count + 1, 1):
                    initial_cow_vol_stats[x] = self.storage_controller.peek("storage/volume/VOL_TYPE_BLK_LOCAL_THIN/{}".
                                                                            format(self.cow_uuid[x]))

                thread_id = {}
                wait_time = 0
                self.host_count = 1
                if "write" not in mode:
                    fio_numjobs = len(self.device_details.split(":")) * 1
                else:
                    fio_numjobs = 1

                for x in range(1, self.host_count + 1, 1):
                    if mode == "rw" or mode == "randrw":
                        wait_time = self.host_count + 1 - x
                        fio_output[combo][mode] = {}
                        self.linux_host_inst[x] = self.linux_host.clone()
                        thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                     func=fio_parser,
                                                                     arg1=self.linux_host_inst[x],
                                                                     filename=self.device_details,
                                                                     rw=mode,
                                                                     rwmixread=self.fio_rwmixread,
                                                                     bs=fio_block_size,
                                                                     iodepth=fio_iodepth,
                                                                     numjobs=fio_numjobs,
                                                                     **self.fio_cmd_args)
                        fun_test.sleep("Fio threadzz", seconds=1)
                    else:
                        wait_time = self.host_count + 1 - x
                        fio_output[combo][mode] = {}
                        self.linux_host_inst[x] = self.linux_host.clone()
                        thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                     func=fio_parser,
                                                                     arg1=self.linux_host_inst[x],
                                                                     filename=self.device_details,
                                                                     rw=mode,
                                                                     bs=fio_block_size,
                                                                     iodepth=fio_iodepth,
                                                                     numjobs=fio_numjobs,
                                                                     **self.fio_cmd_args)
                        fun_test.sleep("Fio Threadzz", seconds=1)
                fun_test.sleep("Sleeping between thread join...", seconds=10)
                for x in range(1, self.host_count + 1, 1):
                    fun_test.log("Joining thread {}".format(x))
                    fun_test.join_thread(fun_test_thread_id=thread_id[x])
                if self.linux_host.command("pgrep fio"):
                    timer_kill = FunTimer(max_time=self.fio_cmd_args["timeout"] * 2)
                    while not timer_kill.is_expired():
                        if not self.linux_host.command("pgrep fio"):
                            break
                        else:
                            fun_test.sleep("Waiting for fio to exit...sleeping 10 secs", seconds=10)
                    fun_test.log("Timer expired, killing fio...")
                    self.linux_host.command("for i in `pgrep fio`;do kill -9 $i;done")
                self.linux_host.disconnect()

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Get base volume stats after fio
                final_base_vol_stats = self.storage_controller.peek("storage/volume/VOL_TYPE_BLK_LOCAL_THIN/{}".
                                                                    format(self.thin_uuid))
                # Create SNAP vol
                if not snap_vol_created:
                    x = 1
                    command_result = self.storage_controller.create_snap_volume(capacity=self.blt_details["capacity"],
                                                                                block_size=self.blt_details["block_size"],
                                                                                name="snap_vol_" + str(x),
                                                                                uuid=self.snap_uuid[x],
                                                                                cow_uuid=self.cow_uuid[x],
                                                                                base_uuid=self.thin_uuid,
                                                                                command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Creation of Snap volume using BV & COW volume".
                                         format(self.snap_uuid[x], self.thin_uuid, self.cow_uuid[x]))
                    snap_vol_created = True
                    fun_test.sleep("Snap vol created")
                    snap_vol_details = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_SNAP/{}".
                                                                    format(self.snap_uuid[x]))
                    if snap_vol_details["data"] is None:
                        fun_test.simple_assert(False, "Snap volume not created")

                    if hasattr(self, "detach_basevol") and self.detach_basevol:
                        temp = self.device_details.split("/")[-1]
                        temp1 = re.search('nvme(.[0-9]*)', temp)
                        nvme_disconnect_device = temp1.group()
                        if nvme_disconnect_device:
                            self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                            nvme_dev_output = get_nvme_device(self.linux_host)
                            if nvme_dev_output:
                                fun_test.critical(False, "NVMe disconnect failed")
                                self.linux_host.disconnect()

                        command_result = self.storage_controller.detach_volume_from_controller(
                            ctrlr_uuid=self.ctrlr_uuid,
                            ns_id=1,
                            command_duration=self.command_timeout)
                        fun_test.test_assert(command_result["status"], "Detach base volume from controller")

                    # Attach snap vol to TCP controller
                    if self.snap_attach:
                        command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                             vol_uuid=self.snap_uuid[x],
                                                                                             ns_id=x + 1,
                                                                                             command_duration=self.command_timeout)
                        fun_test.test_assert(command_result["status"], "Attach Snapvol to controller".format([x]))

                        if hasattr(self, "detach_basevol") and self.detach_basevol:
                            for index, host_name in enumerate(self.host_info):
                                host_handle = self.host_info[host_name]["handle"]
                                fun_test.shared_variables["host_handle"] = host_handle
                                host_ip = self.host_info[host_name]["ip"]
                                nqn = self.nqn_list[index]

                                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                                    command_result = host_handle.sudo_command(
                                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                                            unicode.lower(self.transport_type),
                                            self.test_network["f1_loopback_ip"],
                                            self.transport_port, nqn,
                                            self.nvme_io_queues, host_ip))
                                    fun_test.log(command_result)
                                else:
                                    command_result = host_handle.sudo_command(
                                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(
                                            unicode.lower(self.transport_type),
                                            self.test_network["f1_loopback_ip"],
                                            self.transport_port, nqn, host_ip))
                                    fun_test.log(command_result)
                                fun_test.sleep("Wait for couple of seconds for the snap volume to be accessible to "
                                               "the host")
                                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                                host_handle.sudo_command("dmesg")
                                fun_test.shared_variables["host_handle"] = host_handle
                                self.device_details = get_nvme_device(host_handle)
                                host_handle.disconnect()
                                if not self.device_details:
                                    host_handle.command("dmesg")
                                    fun_test.shared_variables["nvme_discovery"] = False
                                    fun_test.simple_assert(False, "NVMe device not found")
                                else:
                                    fun_test.shared_variables["nvme_discovery"] = True

    def cleanup(self):
        self.linux_host = fun_test.shared_variables["host_handle"]
        self.blt_detach_count = 0
        self.blt_delete_count = 0

        temp = self.device_details.split("/")[-1]
        temp1 = re.search('nvme(.[0-9]*)', temp)
        nvme_disconnect_device = temp1.group()
        if nvme_disconnect_device:
            self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
            nvme_dev_output = get_nvme_device(self.linux_host)
            if nvme_dev_output:
                fun_test.critical(False, "NVMe disconnect failed")
                self.linux_host.disconnect()

        # Detach BV from controller
        if self.bv_attach:
            command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                   ns_id=1,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach base volume from controller")

        for x in range(1, self.snap_count + 1, 1):
            if self.snap_attach:
                command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                       ns_id=x + 1,
                                                                                       command_duration=self.command_timeout)
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_detach_count += 1
                else:
                    fun_test.test_assert(command_result["status"], "Detach Snapvolume with nsid {} from ctrlr".format(x))

            # Delete SNAP volume
            command_result = self.storage_controller.delete_volume(uuid=self.snap_uuid[x],
                                                                   type="VOL_TYPE_BLK_SNAP",
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Delete Snapvolume {}".format(x))
            command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                       command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Delete TCP controller")

            # Delete COW volume
            command_result = self.storage_controller.delete_volume(uuid=self.cow_uuid[x],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_delete_count += 1
            else:
                fun_test.test_assert(not command_result["status"], "Delete COW vol {}".format(x))

        # Delete Base volume
        command_result = self.storage_controller.delete_volume(uuid=self.thin_uuid,
                                                               type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(not command_result["status"], "Delete Base Volume")

        for x in range(1, self.snap_count + 1, 1):
            storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                      "VOL_TYPE_BLK_LOCAL_THIN", self.cow_uuid[x])
            command_result = self.storage_controller.peek(storage_props_tree)
            # changed the expression from command_result["data"] is None
            fun_test.simple_assert(expression=not (bool(command_result["data"])),
                                   message="COW vol {} with uuid {} removal".format(x, self.cow_uuid[x]))

        fun_test.log("Configuration cleaned")


class C12991(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              test_rail_case_ids=["C12991"],
                              summary="Create,Attach,Detach & Delete BLT Snapshot for BLT Base Volume",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')

    def run(self):
        pass


class C35434(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              test_rail_case_ids=["C35434"],
                              summary="Create & Attach Base, Create Snap and Detach Base Volume",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')

    def run(self):
        pass


class C17750(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              test_rail_case_ids=["C17750"],
                              summary="Create BLT Snapshot for BLT base volume without attaching base"
                                      "volume to a controller",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')

    def run(self):
        pass


class C35290(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              test_rail_case_ids=["C35290"],
                              summary="Verify data integrity by sequential read from BLT Snapshot for "
                                      "BLT Base volume before overwriting contents in BV",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')


class C19274(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              test_rail_case_ids=["C19274"],
                              summary="Create BLT Snapshot for BLT base volume after detaching base "
                                      "volume from the controller",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')


if __name__ == "__main__":
    bltscript = Singledpu()
    bltscript.add_test_case(C12991())
    bltscript.add_test_case(C35434())
    bltscript.add_test_case(C17750())
    bltscript.add_test_case(C35290())
    bltscript.add_test_case(C19274())
    bltscript.run()
