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
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
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


# Disconnect linux objects
def fio_parser(arg1, **kwargs):
    arg1.pcie_fio(**kwargs)
    arg1.disconnect()


class BLTCryptoVolumeScript(FunTestScript):
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
            self.disable_wu_watchdog = False
        if "syslog" in job_inputs:
            self.syslog = job_inputs["syslog"]

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
        fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
        fun_test.shared_variables["csi_cache_miss_enabled"] = self.csi_cache_miss_enabled

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            fun_test.shared_variables["perf_listener_host_name"] = self.perf_listener_host_name
            fun_test.shared_variables["perf_listener_ip"] = self.perf_listener_ip

        # for key in self.host_handles:
        #     # Ensure all hosts are up after reboot
        #     fun_test.test_assert(self.host_handles[key].ensure_host_is_up(max_wait_time=self.reboot_timeout),
        #                          message="Ensure Host {} is reachable after reboot".format(key))
        #
        #     # TODO: enable after mpstat check is added
        #     """
        #     # Check and install systat package
        #     install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
        #     fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
        #     """
        #     # Ensure required modules are loaded on host server, if not load it
        #     for module in self.load_modules:
        #         module_check = self.host_handles[key].lsmod(module)
        #         if not module_check:
        #             self.host_handles[key].modprobe(module)
        #             module_check = self.host_handles[key].lsmod(module)
        #             fun_test.sleep("Loading {} module".format(module))
        #         fun_test.simple_assert(module_check, "{} module is loaded".format(module))
        #
        # # Ensuring connectivity from Host to F1's
        # for key in self.host_handles:
        #     for index, ip in enumerate(self.f1_ips):
        #         ping_status = self.host_handles[key].ping(dst=ip)
        #         fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
        #                              format(key, self.funcp_spec[0]["container_names"][index], ip))

        # Ensuring perf_host is able to ping F1 IP
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
            csi_perf_host_instance = Linux(host_ip=self.csi_perf_host_obj.spec["host_ip"],
                                           ssh_username=self.csi_perf_host_obj.spec["ssh_username"],
                                           ssh_password=self.csi_perf_host_obj.spec["ssh_password"])
            ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
            fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                 format(self.perf_listener_host_name, self.csi_f1_ip))

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


class BLTCryptoVolumeTestCase(FunTestCase):
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

        # Setting the list of block size and IO depth combo
        if 'fio_bs_iodepth' not in testcase_dict[testcase] or not testcase_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file.".format(testcase, testcase_file))
        fun_test.test_assert(benchmark_parsing, "Parsing testcase json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))

        if self.blt_details["encrypt"] == "enable" or self.blt_details["encrypt"] == "alternate":
            if ('expected_decryption_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_decryption_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected decryption stats for {} testcase is not available in the {} file".
                                  format(testcase, testcase_dict))
            if ('expected_encryption_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_encryption_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected encryption stats for {} testcase is not available in the {} file".
                                  format(testcase, testcase_dict))

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
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "capacity" in job_inputs:
            self.blt_details["capacity"] = job_inputs["capacity"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "warm_up_traffic" in job_inputs:
            self.warm_up_traffic = job_inputs["warm_up_traffic"]
        if "warm_up_count" in job_inputs:
            self.warm_up_count = job_inputs["warm_up_count"]
        if "runtime" in job_inputs:
            self.fio_cmd_args["runtime"] = job_inputs["runtime"]
            self.fio_cmd_args["timeout"] = self.fio_cmd_args["runtime"] + 60
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        self.linux_host_inst = {}

        key256_count = 0
        key384_count = 0
        key512_count = 0
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0
        self.correct_key_tweak = None
        self.blt_creation_fail = None

        # Configuring local thin block volume
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")
        # Configuring controller
        if not fun_test.shared_variables["ctrl_created"]:
            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")
            fun_test.shared_variables["ctrl_created"] = True

        # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
        # number of volumes by repeating the existing entries for the required number of times
        self.final_host_ips = self.host_ips[:]
        if len(self.host_ips) < self.blt_count:
            for i in range(len(self.host_ips), self.blt_count):
                self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])
        for host_name in self.host_info:
            self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(self.host_info[host_name]["ip"])

        # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
        # the capacity is not overridden while starting the script
        # min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
        # if min_drive_capacity:
        #     self.blt_details["capacity"] = min_drive_capacity
        #     # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
        #     self.blt_details["capacity"] -= self.drive_margin
        # else:
        #     fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
        #                       "given in the script config file or capacity passed at the runtime...")
        # if "capacity" in job_inputs:
        #     fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
        #                       "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
        #     self.blt_details["capacity"] = job_inputs["capacity"]

        self.thin_uuid = {}
        self.block_size = {}
        self.vol_capacity = {}
        self.encrypted_vol = {}
        # Create one TCP controller per host
        self.nvme_block_device = []
        self.ctrlr_uuid = []
        self.nqn_list = []
        bs_auto = None
        capacity_auto = None
        fun_test.shared_variables["nvme_discovery"] = False

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
        fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                             format(self.remote_ip, self.ctrlr_uuid))

        for x in range(1, self.blt_count + 1, 1):
            self.thin_uuid[x] = utils.generate_uuid()
            # Key generation for encryption based on size or input is random or alternate
            if self.key_size == "random":
                key_range = [32, 48, 64]
                rand_key = random.choice(key_range)
                self.xts_key = utils.generate_key(rand_key)
                if rand_key == 32:
                    key256_count += 1
                elif rand_key == 48:
                    key384_count += 1
                else:
                    key512_count += 1
            elif self.key_size == "alternate":
                if x % 2:
                    key256_count += 1
                    self.xts_key = utils.generate_key(32)
                elif x % 3:
                    key384_count += 1
                    self.xts_key = utils.generate_key(48)
                elif x % 5:
                    key512_count += 1
                    self.xts_key = utils.generate_key(64)
            else:
                self.xts_key = utils.generate_key(self.key_size)
            self.xts_tweak = utils.generate_key(self.xtweak_size)

            # Select volume block size from a range
            if self.blt_details["block_size"] == "Auto":
                bs_auto = True
                self.block_size[x] = random.choice(self.blt_details["block_size_range"])
                self.blt_details["block_size"] = self.block_size[x]

            # Select volume capacity from a range
            if self.blt_details["capacity"] == "Auto":
                capacity_auto = True
                self.vol_capacity[x] = random.choice(self.blt_details["capacity_range"])
                self.blt_details["capacity"] = self.vol_capacity[x]
                check_cap = self.blt_details["capacity"] % self.blt_details["block_size"]
                fun_test.simple_assert(expression=check_cap == 0,
                                       message="Capacity should be multiple of block size.")
            # Here you cannot use boolean coz when encryption is set to alternate in json the value always
            # returns true as something is assigned to it.
            if self.blt_details["encrypt"] == "enable":
                self.vol_encrypt = True
                self.encrypted_vol[x] = self.thin_uuid[x]
            elif self.blt_details["encrypt"] == "disable":
                self.vol_encrypt = False
            elif self.blt_details["encrypt"] == "alternate":
                if x % 2:
                    self.vol_encrypt = True
                    self.encrypted_vol[x] = self.thin_uuid[x]
                else:
                    self.vol_encrypt = False
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(x),
                                                                   uuid=self.thin_uuid[x],
                                                                   encrypt=self.vol_encrypt,
                                                                   key=self.xts_key,
                                                                   xtweak=self.xts_tweak,
                                                                   command_duration=self.command_timeout)
            if bs_auto:
                self.blt_details["block_size"] = "Auto"
            if capacity_auto:
                self.blt_details["capacity"] = "Auto"

            # Attach volume only if encryption is disabled or key/tweak sizes are sane
            if (self.key_size == 32 or self.key_size == 48 or self.key_size == 64 or self.key_size == "random" or
                self.key_size == "alternate" or not self.vol_encrypt) and self.xtweak_size == 8:
                self.correct_key_tweak = True
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"], "BLT {} creation with uuid {} & capacity {}".
                                         format(x, self.thin_uuid[x], self.blt_details["capacity"]))

                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     vol_uuid=self.thin_uuid[x],
                                                                                     ns_id=x,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to the host {} via controller "
                                                               "{}".format(self.thin_uuid[x],
                                                                           self.remote_ip,
                                                                           self.ctrlr_uuid))
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_attach_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Attach BLT {} with uuid {}".
                                         format(x, self.thin_uuid[x]))
            elif self.vol_encrypt:
                fun_test.test_assert(not command_result["status"],
                                     message="BLT creation should fail")
                self.blt_creation_fail = True
            else:
                self.blt_create_count += 1
                fun_test.test_assert(command_result["status"], "BLT {} creation with uuid {} & capacity {} "
                                                               "with encryption disabled".
                                     format(x, self.thin_uuid[x], self.blt_details["capacity"]))

        if self.key_size == "random" or self.key_size == "alternate":
            fun_test.log("Total BLT with 256 bit key: {}".format(key256_count))
            fun_test.log("Total BLT with 384 bit key: {}".format(key384_count))
            fun_test.log("Total BLT with 512 bit key: {}".format(key512_count))
        if not self.blt_creation_fail:
            fun_test.test_assert_expected(self.blt_count, self.blt_create_count,
                                          message="BLT count and create count")
        if self.correct_key_tweak:
            fun_test.test_assert_expected(self.blt_count, self.blt_attach_count,
                                          message="BLT count and attach count")

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                command_result = self.storage_controller.set_fcp_scheduler(fcp_sch_config=self.config_fcp_scheduler,
                                                                           command_timeout=self.command_timeout)
                if not command_result["status"]:
                    fun_test.critical("Unable to set the fcp scheduler bandwidth...So proceeding the test with the "
                                      "default setting")
                elif self.config_fcp_scheduler != command_result["data"]:
                    fun_test.critical("Unable to fetch the applied FCP scheduler config... So proceeding the test "
                                      "with the default setting")
                else:
                    fun_test.log("Successfully set the fcp scheduler bandwidth to: {}".format(command_result["data"]))

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                fun_test.shared_variables["host_handle"] = host_handle
                host_ip = self.host_info[host_name]["ip"]
                nqn = self.nqn_list[index]
                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")

                # Stop udev services on host
                service_list = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
                for service in service_list:
                    service_status = host_handle.systemctl(service_name=service, action="stop")
                    fun_test.simple_assert(service_status,
                                           "Stopping {} service".format(service))

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

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        self.linux_host = fun_test.shared_variables["host_handle"]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_output = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}
        diff_volume_stats = {}
        diff_crypto_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}

        for combo in self.fio_bs_iodepth:
            fio_output[combo] = {}
            final_volume_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}
            diff_volume_stats[combo] = {}
            diff_crypto_stats[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            if self.blt_details["encrypt"] == "enable" or self.blt_details["encrypt"] == "alternate":
                if combo in self.expected_decryption_stats:
                    expected_decryption_stats = self.expected_decryption_stats[combo]
                else:
                    expected_decryption_stats = self.expected_decryption_stats

                if combo in self.expected_encryption_stats:
                    expected_encryption_stats = self.expected_encryption_stats[combo]
                else:
                    expected_encryption_stats = self.expected_encryption_stats

            for mode in self.fio_modes:
                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                for loop in range(0, self.fio_loop, 1):
                    fun_test.log("Running loop {} of {}".format((loop+1), self.fio_loop))
                    initial_volume_stats[combo][mode] = {}
                    for x in range(1, self.blt_count + 1, 1):
                        initial_volume_stats[combo][mode][x] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial BLT {} stats of DUT".format(x))
                        initial_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("BLT {} Stats at the beginning of the test: {}".
                                     format(x, initial_volume_stats[combo][mode][x]))

                    initial_crypto_stats[combo][mode] = {}
                    if self.blt_details["encrypt"] == "enable" or self.blt_details["encrypt"] == "alternate":
                        self.crypto_ops = ["encryption", "decryption"]
                        for i in self.encrypted_vol:
                            initial_crypto_stats[combo][mode][i] = {}
                            for x in self.crypto_ops:
                                initial_crypto_stats[combo][mode][i][x] = {}
                                crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                            "VOL_TYPE_BLK_LOCAL_THIN",
                                                                            self.thin_uuid[i], x)

                                command_result = self.storage_controller.peek(crypto_props_tree)
                                fun_test.simple_assert(command_result["status"], "Initial {} stats for BLT {}".
                                                       format(x, i))
                                if command_result["data"] is None:
                                    command_result["data"] = 0
                                initial_crypto_stats[combo][mode][i][x] = command_result["data"]

                                fun_test.log("BLT {} crypto stats at the beginning of the test: {}".
                                             format(i, initial_crypto_stats[combo][mode][i]))

                    fun_test.log("Running fio test is threaded mode...")
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

                    # Moved the detach loop here as the BLT crypto stats get reset to 0 during detach/attach
                    if self.detach_vol:
                        fun_test.sleep("Sleeping for {} seconds before detach/attach".format(self.iter_interval),
                                       self.iter_interval)
                        # Disconnect from host
                        if fun_test.shared_variables["nvme_discovery"]:
                            temp = self.device_details.split("/")[-1]
                            temp1 = re.search('nvme(.[0-9]*)', temp)
                            nvme_disconnect_device = temp1.group()
                            if nvme_disconnect_device:
                                self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                                nvme_dev_output = get_nvme_device(self.linux_host)
                                if nvme_dev_output:
                                    fun_test.critical(False, "NVMe disconnect failed")
                                    self.linux_host.disconnect()
                                else:
                                    fun_test.shared_variables["nvme_discovery"] = False
                        for x in range(1, self.blt_count + 1, 1):
                            command_result = self.storage_controller.detach_volume_from_controller(
                                ctrlr_uuid=self.ctrlr_uuid,
                                ns_id=x,
                                command_duration=self.command_timeout)
                            fun_test.simple_assert(command_result["status"],
                                                   message="Volume detach failed for test {} with combo {}".
                                                   format(mode, combo))

                            command_result = self.storage_controller.attach_volume_to_controller(
                                ctrlr_uuid=self.ctrlr_uuid,
                                vol_uuid=self.thin_uuid[x],
                                ns_id=x,
                                command_duration=self.command_timeout)
                            fun_test.log(command_result)
                            fun_test.simple_assert(command_result["status"],
                                                   message="Volume attach failed for test {} with combo {}".
                                                   format(mode, combo))

                        for index, host_name in enumerate(self.host_info):
                            host_handle = self.host_info[host_name]["handle"]
                            fun_test.shared_variables["host_handle"] = host_handle
                            host_ip = self.host_info[host_name]["ip"]
                            nqn = self.nqn_list[index]

                            host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
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

    def cleanup(self):
        bs_auto = None
        capacity_auto = None

        self.linux_host = fun_test.shared_variables["host_handle"]

        if not self.blt_creation_fail:
            # Not using attach count as for TC 17 attach is not done but still BLT is created.
            for x in range(1, self.blt_create_count + 1, 1):
                if self.correct_key_tweak:
                    if fun_test.shared_variables["nvme_discovery"]:
                        temp = self.device_details.split("/")[-1]
                        temp1 = re.search('nvme(.[0-9]*)', temp)
                        nvme_disconnect_device = temp1.group()
                        if nvme_disconnect_device:
                            self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                            nvme_dev_output = get_nvme_device(self.linux_host)
                            if nvme_dev_output:
                                fun_test.critical(False, "NVMe disconnect failed")
                                self.linux_host.disconnect()
                            else:
                                fun_test.shared_variables["nvme_discovery"] = False

                    command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                           ns_id=x,
                                                                                           command_duration=self.command_timeout)

                    fun_test.log(command_result)
                    if command_result["status"]:
                        self.blt_detach_count += 1
                    else:
                        fun_test.test_assert(command_result["status"], "Detach BLT {} with nsid {} from ctrlr".
                                             format(self.thin_uuid[x], x))

                if self.blt_details["block_size"] == "Auto":
                    bs_auto = True
                    self.blt_details["block_size"] = self.block_size[x]

                if self.blt_details["capacity"] == "Auto":
                    capacity_auto = True
                    self.blt_details["capacity"] = self.vol_capacity[x]

                command_result = self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=self.thin_uuid[x],
                                                                       type="VOL_TYPE_BLK_LOCAL_THIN")
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_delete_count += 1
                else:
                    fun_test.test_assert(not command_result["status"], "Delete BLT {} with uuid {}".
                                         format(x, self.thin_uuid[x]))

                if bs_auto:
                    self.blt_details["block_size"] = "Auto"
                if capacity_auto:
                    self.blt_details["capacity"] = "Auto"

            try:
                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Delete of controller")
            except:
                fun_test.critical("Controller failed to get deleted")

            if self.correct_key_tweak:
                fun_test.test_assert_expected(self.blt_count, self.blt_detach_count,
                                              message="BLT count & detach count")

            fun_test.test_assert_expected(self.blt_count, self.blt_delete_count,
                                          message="BLT count & delete count")

            for x in range(1, self.blt_count + 1, 1):
                storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                          "VOL_TYPE_BLK_LOCAL_THIN", self.thin_uuid[x])
                command_result = self.storage_controller.peek(storage_props_tree)
                # changed the expression from command_result["data"] is None
                fun_test.simple_assert(expression=not(bool(command_result["data"])),
                                       message="BLT {} with uuid {} removal".format(x, self.thin_uuid[x]))


class BLTKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a volume with 256 bit key and run FIO on single BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a local thin block volume with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create BLT's with encryption using 256 bit key & run RW test on single volume "
                                      "using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create BLT's with encryption using 256 bit key & run RandRW test using "
                                      "different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey384(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create BLT's with encryption using 384 bit key & run RandRW test using "
                                      "different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey384RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Create BLT's with encryption using 384 bit key & run RW test on single volume "
                                      "using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey384RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create BLT's with encryption using 384 bit key & run RandRW test using "
                                      "different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create a volume with 512 bit key and run FIO on single BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a local thin block volume with encryption using 512 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Create BLT's with encryption using 512 bit key & run RW test on single volume "
                                      "using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Create BLT's with encryption using 512 bit key & run RandRW test on single "
                                      "volume using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class WrongKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Create BLT's with wrong size key",
                              steps='''
                              1. Create a BLT with encryption using unsupported key in dut.
        ''')

    def run(self):
        pass


class WrongTweak(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Create BLT's with wrong size tweak",
                              steps='''
                              1. Create a BLT with encryption using unsupported tweak in dut.
        ''')

    def run(self):
        pass


class CreateDelete256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="Create, attach & delete 25 BLT's with encryption using 256 size key",
                              steps='''
                              1. Create BLT's with encryption with 256 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def run(self):
        pass


class CreateDelete384(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=13,
                              summary="Create, attach & delete 25 BLT's with encryption using 384 size key",
                              steps='''
                              1. Create BLT's with encryption with 384 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def run(self):
        pass


class CreateDelete512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=14,
                              summary="Create, attach & delete 25 BLT's with encryption using 512 size key",
                              steps='''
                              1. Create BLT's with encryption with 512 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def run(self):
        pass


class MultipleBLT256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=15,
                              summary="Create BLT's with 256 bit key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=16,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=17,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RandRW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT384(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=18,
                              summary="Create BLT's with 384 bit key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT384RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=19,
                              summary="Create multiple BLT's with encryption using 384 bit key & run FIO in parallel "
                                      "on all BLT RW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT384RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=20,
                              summary="Create multiple BLT's with encryption using 384 bit key & run FIO in parallel "
                                      "on all BLT RandRW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 384 bit key in dut.
                              2. Attach it to external linux/container.
        ''')


class MultipleBLT512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=21,
                              summary="Create BLT's with 512 bit key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=22,
                              summary="Create multiple BLT's with encryption using 512 bit key & run FIO in parallel "
                                      "on all BLT RW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=23,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RandRW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class EncryptDisable(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=24,
                              summary="Create BLT's with wrong size key/tweak with encryption disabled",
                              steps='''
                              1. Create a BLT with encryption disabled using unsupported tweak in dut.
                              2. Creation of BLT should pass as encryption is disabled.
        ''')

    def run(self):
        pass


class BLTRandomKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=25,
                              summary="Create BLT's with random key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using random key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class MultiVolRandKeyRandCap(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=26,
                              summary="Create BLT's with random key & capacity and run FIO on single BLT with write,"
                                      "read,randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
        ''')


class BLTFioDetach(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=27,
                              summary="Create BLT's with random key & capacity & run FIO in parallel with write,read,"
                                      "randwrite/read pattern, block size & depth with detach after each iteration",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTFioEncZeroPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=28,
                              summary="Encrypt multiple BLT with random key and run fio with different RW pattern,"
                                      "(write,read,randwrite/read), block size & depth with 0x000000000 pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTFioEncDeadBeefPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=29,
                              summary="Encrypt multiple BLT with random key and run fio with different RW pattern"
                                      "(write,read,randwrite/read),block size & depth with DEADBEEF pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTAlternateEncrypt(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=30,
                              summary="Encrypt alternate BLT with random key & run fio with different RW pattern"
                                      "(write,read,randwrite/read),block size & depth with DEADBEEF pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class MultiVolRandKeyUnaligned(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=31,
                              summary="Create BLT's with random key & capacity and run FIO on single BLT with write,"
                                      "read,randwrite/read pattern, with unaligned block size",
                              steps='''
                                        1. Create 8 BLT with rand capacity & rand encryption key.
                                        2. Attach it to external linux/container.
                                        3. Run Fio with different block size & IO depth in parallel.
                                      ''')


class MultiVolRandKeyAesUnaligned(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=32,
                              summary="Create BLT's with random key & capacity and run FIO on single BLT with write,"
                                      "read,randwrite/read pattern, with AES unaligned block size",
                              steps='''
                                        1. Create 8 BLT with rand capacity & rand encryption key.
                                        2. Attach it to external linux/container.
                                        3. Run Fio with different block size & IO depth in parallel.
                                      ''')


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(BLTKey256())
    bltscript.add_test_case(BLTKey256RW())
    bltscript.add_test_case(BLTKey256RandRW())
    bltscript.add_test_case(BLTKey384())
    bltscript.add_test_case(BLTKey384RW())
    bltscript.add_test_case(BLTKey384RandRW())
    bltscript.add_test_case(BLTKey512())
    bltscript.add_test_case(BLTKey512RW())
    bltscript.add_test_case(BLTKey512RandRW())
    bltscript.add_test_case(WrongKey())
    bltscript.add_test_case(WrongTweak())
    bltscript.add_test_case(CreateDelete256())
    bltscript.add_test_case(CreateDelete384())
    bltscript.add_test_case(CreateDelete512())
    bltscript.add_test_case(MultipleBLT256())
    bltscript.add_test_case(MultipleBLT256RW())
    bltscript.add_test_case(MultipleBLT256RandRW())
    bltscript.add_test_case(MultipleBLT384())
    bltscript.add_test_case(MultipleBLT384RW())
    bltscript.add_test_case(MultipleBLT384RandRW())
    bltscript.add_test_case(MultipleBLT512())
    bltscript.add_test_case(MultipleBLT512RW())
    bltscript.add_test_case(MultipleBLT512RandRW())
    bltscript.add_test_case(EncryptDisable())
    bltscript.add_test_case(BLTRandomKey())
    bltscript.add_test_case(MultiVolRandKeyRandCap())
    bltscript.add_test_case(BLTFioDetach())
    bltscript.add_test_case(BLTFioEncZeroPattern())
    bltscript.add_test_case(BLTFioEncDeadBeefPattern())
    bltscript.add_test_case(BLTAlternateEncrypt())
    bltscript.add_test_case(MultiVolRandKeyUnaligned())
    bltscript.add_test_case(MultiVolRandKeyAesUnaligned())

    bltscript.run()
