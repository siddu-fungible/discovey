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

        self.thin_uuid = {}
        self.cow_uuid = {}
        self.snap_uuid = {}
        self.block_size = {}
        self.vol_capacity = {}
        # Create one TCP controller per host
        self.nvme_block_device = []
        self.ctrlr_uuid = []
        self.nqn_list = []
        bs_auto = None
        capacity_auto = None

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
            self.cow_uuid[x] = utils.generate_uuid()
            self.snap_uuid[x] = utils.generate_uuid()

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
            # Create Base volume
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block_" + str(x),
                                                                   uuid=self.thin_uuid[x],
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Base volume with uuid {}".format(self.thin_uuid[x]))

            # Create COW volume
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="cow_vol_" + str(x),
                                                                   uuid=self.cow_uuid[x],
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "COW volume with uuid {}".format(self.cow_uuid[x]))

            # Attach Base volume to controller before creating SNAP volume
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 vol_uuid=self.thin_uuid[x],
                                                                                 ns_id=x,
                                                                                 command_duration=self.command_timeout)

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
        snap_vol_created = False
        check_test_mode = []

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_output = {}
        diff_volume_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}

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
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

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

                # Create SNAP vol
                if not snap_vol_created:
                    x = 1
                    command_result = self.storage_controller.create_snap_volume(capacity=self.blt_details["capacity"],
                                                                                block_size=self.blt_details["block_size"],
                                                                                name="snap_vol_" + str(x),
                                                                                uuid=self.snap_uuid[x],
                                                                                cow_uuid=self.cow_uuid[x],
                                                                                base_uuid=self.thin_uuid[x],
                                                                                command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Snap volume with uuid {} using BV : {} & COW : {}".
                                         format(self.cow_uuid[x], self.thin_uuid[x], self.cow_uuid[x]))
                    snap_vol_created = True
                    fun_test.sleep("Snap vol created")

    def cleanup(self):
        bs_auto = None
        capacity_auto = None

        self.linux_host = fun_test.shared_variables["host_handle"]

        for x in range(1, self.blt_count + 1, 1):
            temp = self.device_details.split("/")[-1]
            temp1 = re.search('nvme(.[0-9]*)', temp)
            nvme_disconnect_device = temp1.group()
            if nvme_disconnect_device:
                self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                nvme_dev_output = get_nvme_device(self.linux_host)
                if nvme_dev_output:
                    fun_test.critical(False, "NVMe disconnect failed")
                    self.linux_host.disconnect()
            command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                   ns_id=x,
                                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_detach_count += 1
            else:
                fun_test.test_assert(command_result["status"], "Detach BLT {} with nsid {} from ctrlr".
                                     format(self.thin_uuid[x], x))
            # Delete SNAP volume
            command_result = self.storage_controller.delete_volume(uuid=self.snap_uuid[x],
                                                                   type="VOL_TYPE_BLK_SNAP",
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Delete snap volume {}".format(x))
            command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                       command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Delete of controller")
            # Delete COW volume
            command_result = self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="cow_vol" + str(x),
                                                                   uuid=self.cow_uuid[x],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_delete_count += 1
            else:
                fun_test.test_assert(not command_result["status"], "Delete COW vol {} with uuid {}".
                                     format(x, self.cow_uuid[x]))
            # Delete Base volume
            command_result = self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(x),
                                                                   uuid=self.thin_uuid[x],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_delete_count += 1
            else:
                fun_test.test_assert(not command_result["status"], "Delete BV {} with uuid {}".
                                     format(x, self.thin_uuid[x]))

        for x in range(1, self.blt_count + 1, 1):
            storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                      "VOL_TYPE_BLK_LOCAL_THIN", self.thin_uuid[x])
            command_result = self.storage_controller.peek(storage_props_tree)
            # changed the expression from command_result["data"] is None
            fun_test.simple_assert(expression=not (bool(command_result["data"])),
                                   message="BV {} with uuid {} removal".format(x, self.thin_uuid[x]))
            storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                      "VOL_TYPE_BLK_LOCAL_THIN", self.cow_uuid[x])
            command_result = self.storage_controller.peek(storage_props_tree)
            # changed the expression from command_result["data"] is None
            fun_test.simple_assert(expression=not (bool(command_result["data"])),
                                   message="COW vol {} with uuid {} removal".format(x, self.thin_uuid[x]))


class SnapVolCreation(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a SNAP volume without FunOS crashing",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV
                              4. Create a SNAP volume
        ''')


class SnapVolRead(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Perform a read from BV after snapshot creation",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV and write data on entire disk
                              4. Create a SNAP volume
                              5. On host read from volume
        ''')


class SnapVolDiffWrite(SnapVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Perform a write to BV after snapshot creation",
                              steps='''
                              1. Create a BLT for base volume & then a BLT for COW volume.
                              2. Attach the BV to controller
                              3. Connect from host to BV and write data on entire disk
                              4. Create a SNAP volume
                              5. On host write to the volume
        ''')


if __name__ == "__main__":
    bltscript = Singledpu()
    # bltscript.add_test_case(SnapVolCreation())
    bltscript.add_test_case(SnapVolRead())
    bltscript.add_test_case(SnapVolDiffWrite())
    bltscript.run()
