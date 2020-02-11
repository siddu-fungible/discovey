from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.security.xts_openssl_template import XtsOpenssl
from lib.templates.storage.storage_controller_api import *
import random


def fio_parser(arg1, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"] = fio_output
    fun_test.simple_assert(fio_output, "Fio result")
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
        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        if "deadbeef" in job_inputs:
            fun_test.shared_variables["data_pattern"] = job_inputs["deadbeef"]
        else:
            fun_test.shared_variables["data_pattern"] = False

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
        fun_test.shared_variables["xts_ssl"] = False

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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

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
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

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
        self.nqn = self.nvme_subsystem
        command_result = self.storage_controller.create_controller(ctrlr_id=1,
                                                                   ctrlr_uuid=self.ctrlr_uuid,
                                                                   ctrlr_type="BLOCK",
                                                                   transport=self.transport_type.upper(),
                                                                   remote_ip=self.remote_ip,
                                                                   subsys_nqn=self.nqn,
                                                                   host_nqn=self.remote_ip,
                                                                   port=self.transport_port,
                                                                   command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                             format(self.remote_ip, self.ctrlr_uuid))

        for x in range(1, self.blt_count + 1, 1):
            self.thin_uuid[1] = utils.generate_uuid()
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
                self.encrypted_vol[x] = self.thin_uuid[1]
            elif self.blt_details["encrypt"] == "disable":
                self.vol_encrypt = False
            elif self.blt_details["encrypt"] == "alternate":
                if x % 2:
                    self.vol_encrypt = True
                    self.encrypted_vol[x] = self.thin_uuid[1]
                else:
                    self.vol_encrypt = False
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(x),
                                                                   uuid=self.thin_uuid[1],
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
                                         format(x, self.thin_uuid[1], self.blt_details["capacity"]))

                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     vol_uuid=self.thin_uuid[1],
                                                                                     ns_id=x,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to the host {} via controller "
                                                               "{}".format(self.thin_uuid[1],
                                                                           self.remote_ip,
                                                                           self.ctrlr_uuid))
                fun_test.test_assert(command_result["status"], "Attach BLT {} with uuid {}".
                                     format(x, self.thin_uuid[1]))

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                fun_test.shared_variables["host_handle"] = host_handle
                host_ip = self.host_info[host_name]["ip"]
                nqn = self.nqn
                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")

                # Remove *.txt files from /tmp
                host_handle.sudo_command("rm -rf /tmp/*")

                if not fun_test.shared_variables["xts_ssl"]:
                    self.xts_ssl_template = XtsOpenssl(host_handle)
                    install_status = self.xts_ssl_template.install_ssl()
                    fun_test.test_assert(install_status, "Openssl installation")
                    fun_test.shared_variables["xts_ssl"] = True
                else:
                    self.xts_ssl_template = XtsOpenssl(host_handle)

                # Stop udev services on host
                service_list = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
                for service in service_list:
                    service_status = host_handle.systemctl(service_name=service, action="stop")
                    fun_test.simple_assert(service_status,
                                           "Stopping {} service".format(service))

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
                filesuffix = datetime.now().strftime("%Y%m%d-%H%M%S")
                nvme_connect_filename = "nvme_connect_auto_" + str(filesuffix)
                host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w {}.pcap".
                                             format(nvme_connect_filename))
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                                  self.test_network["f1_loopback_ip"],
                                                                                  self.transport_port, self.nqn,
                                                                                  self.nvme_io_queues, host_ip))
                    fun_test.log(command_result)
                else:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            self.transport_port, self.nqn, host_ip))
                    fun_test.log(command_result)
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                host_handle.sudo_command("dmesg")
                fun_test.shared_variables["host_handle"] = host_handle
                self.device_details = fetch_nvme_list(host_handle)
                host_handle.disconnect()
                if not self.device_details["status"]:
                    host_handle.command("dmesg")
                    fun_test.shared_variables["nvme_discovery"] = False
                    fun_test.simple_assert(False, "NVMe device not found")
                else:
                    fun_test.shared_variables["nvme_discovery"] = True
                    fun_test.shared_variables["nvme_device"] = self.device_details["nvme_device"]
                    fun_test.shared_variables["host_ip"] = host_ip

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        self.linux_host = fun_test.shared_variables["host_handle"]
        nvme_block_device = fun_test.shared_variables["nvme_device"]
        self.host_ip = fun_test.shared_variables["host_ip"]

        self.qemu = QemuStorageTemplate(host=self.linux_host, dut=0)

        temp = self.device_details["nvme_device"].split("/")[-1]
        temp1 = re.search('nvme(.[0-9]*)', temp)
        self.nvme_disconnect_device = temp1.group()

        # Create a file on host used as input for nvme write
        if fun_test.shared_variables["data_pattern"]:
            fun_test.log("Create a input with pattern DEADBEEF")
            self.linux_host.command("while true ; do printf DEADBEEF; done | head -c {} > /tmp/input_file.txt".
                                    format(self.write_size))
        else:
            fun_test.log("Create a input with random chars from urandom file")
            self.linux_host.command("tr -dc A-Za-z0-9 < /dev/urandom | head -c {} > /tmp/input_file.txt".
                                    format(self.write_size))
        self.md5sum_input = self.linux_host.md5sum(file_name="/tmp/input_file.txt")
        fun_test.simple_assert(self.md5sum_input, "Computing md5sum for input file")
        fun_test.log("The md5sum of the input file is {}".format(self.md5sum_input))

        blt_write = {}
        blt_read = {}
        blt_read_cipher = {}
        blt_read_plain = {}
        md5sum_cipher = []
        total_num_blocks = self.data_size / self.write_size
        write_block_count = self.write_size / self.blt_details["block_size"]

        # Do a NVMe write/read based on total num of blocks
        start_count = 0
        for i in range(0, total_num_blocks, 1):
            blk_count = write_block_count - 1
            blt_write[i] = {}
            blt_read[i] = {}
            blt_read_cipher[i] = {}
            blt_read_plain[i] = {}

            blt_write[i] = self.qemu.nvme_write(device=nvme_block_device,
                                                start=start_count,
                                                count=blk_count,
                                                size=self.write_size,
                                                data="/tmp/input_file.txt")
            fun_test.test_assert(expression=blt_write[i] == "Success",
                                 message="Write status : {}, on BLT".format(blt_write[i]))

            blt_read[i] = self.qemu.nvme_read(device=nvme_block_device,
                                              start=start_count,
                                              count=blk_count,
                                              size=self.write_size,
                                              data="/tmp/read_blt" + "_lba_" + str(start_count))
            fun_test.test_assert(expression=blt_write[i] == "Success",
                                 message="Read status : {}, on BLT, LBA {}".format(blt_read[i], start_count))

            self.md5sum_output = self.linux_host.md5sum(file_name="/tmp/read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(self.md5sum_output, "Computing md5sum for output file")
            fun_test.simple_assert(expression=self.md5sum_input == self.md5sum_output,
                                   message="The md5sum doesn't match for LBA {}, input {}, output {}".
                                   format(start_count, self.md5sum_input, self.md5sum_output))

            # Now umount volume and mount without encryption
            self.linux_host.sudo_command("nvme disconnect -d {}".format(self.nvme_disconnect_device))
            nvme_dev_output = fetch_nvme_list(self.linux_host)
            if nvme_dev_output["status"]:
                fun_test.critical(False, "NVMe disconnect failed")
                self.linux_host.disconnect()
            else:
                fun_test.shared_variables["nvme_discovery"] = False

            command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                   ns_id=1,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach BLT with uuid {}".format(self.thin_uuid[1]))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                  capacity=self.blt_details["capacity"],
                                                                  block_size=self.blt_details["block_size"],
                                                                  name="thin_block1",
                                                                  uuid=self.thin_uuid[1],
                                                                  command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Mount BLT without encryption")

            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 ns_id=1,
                                                                                 vol_uuid=self.thin_uuid[1],
                                                                                 command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Attaching BLT without encryption")

            # NVME connect from host
            filesuffix = datetime.now().strftime("%Y%m%d-%H%M%S")
            nvme_connect_filename = "nvme_connect_auto_" + str(filesuffix)
            self.linux_host.start_bg_process(command="sudo tcpdump -i enp216s0 -w {}.pcap".
                                             format(nvme_connect_filename))
            if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                command_result = self.linux_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                              self.test_network["f1_loopback_ip"],
                                                                              self.transport_port, self.nqn,
                                                                              self.nvme_io_queues, self.host_ip))
                fun_test.log(command_result)
            else:
                command_result = self.linux_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                        self.test_network["f1_loopback_ip"],
                                                                        self.transport_port, self.nqn, self.host_ip))
                fun_test.log(command_result)
            fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
            self.linux_host.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
            self.device_details = fetch_nvme_list(self.linux_host)
            fun_test.simple_assert(self.device_details["status"], "NVMe connect after BLT mount without encryption")
            nvme_block_device = self.device_details["nvme_device"]

            blt_read_cipher[i] = self.qemu.nvme_read(device=nvme_block_device,
                                                     start=start_count,
                                                     count=blk_count,
                                                     size=self.write_size,
                                                     data="/tmp/enc_read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=blt_read_cipher[i] == "Success",
                                   message="Cipher Read failed with {} on BLT, LBA {}".
                                   format(blt_read_cipher[i], start_count))

            cipher_md5sum = self.linux_host.md5sum(file_name="/tmp/enc_read_blt" + "_lba_" + str(start_count))
            md5sum_cipher.append(cipher_md5sum)

            # Mount BLT with encryption now
            self.linux_host.sudo_command("nvme disconnect -d {}".format(self.nvme_disconnect_device))
            nvme_dev_output = fetch_nvme_list(self.linux_host)
            if nvme_dev_output["status"]:
                fun_test.critical(False, "NVMe disconnect failed")
                self.linux_host.disconnect()
            else:
                fun_test.shared_variables["nvme_discovery"] = False

            command_result = self.storage_controller.detach_volume_from_controller(ns_id=1,
                                                                                   ctrlr_uuid=self.ctrlr_uuid,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach BLT with uuid {}".format(self.thin_uuid[1]))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                  capacity=self.blt_details["capacity"],
                                                                  block_size=self.blt_details["block_size"],
                                                                  name="thin_block1",
                                                                  encrypt=True,
                                                                  key=self.xts_key,
                                                                  xtweak=self.xts_tweak,
                                                                  uuid=self.thin_uuid[1],
                                                                  command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Mount BLT with encryption")

            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 ns_id=1,
                                                                                 vol_uuid=self.thin_uuid[1],
                                                                                 command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Attaching BLT with encryption")

            # NVME connect from host
            filesuffix = datetime.now().strftime("%Y%m%d-%H%M%S")
            nvme_connect_filename = "nvme_connect_auto_" + str(filesuffix)
            self.linux_host.start_bg_process(command="sudo tcpdump -i enp216s0 -w {}.pcap".
                                             format(nvme_connect_filename))
            if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                command_result = self.linux_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                              self.test_network["f1_loopback_ip"],
                                                                              self.transport_port, self.nqn,
                                                                              self.nvme_io_queues, self.host_ip))
                fun_test.log(command_result)
            else:
                command_result = self.linux_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                        self.test_network["f1_loopback_ip"],
                                                                        self.transport_port, self.nqn, self.host_ip))
                fun_test.log(command_result)
            fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
            self.linux_host.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
            self.device_details = fetch_nvme_list(self.linux_host)
            fun_test.simple_assert(self.device_details["status"], "NVMe connect after BLT mount with encryption")
            nvme_block_device = self.device_details["nvme_device"]

            blt_read_plain[i] = self.qemu.nvme_read(device=nvme_block_device,
                                                    start=start_count,
                                                    count=blk_count,
                                                    size=self.write_size,
                                                    data="/tmp/plain_read_blt" + "_lba_" + str(start_count))
            fun_test.test_assert(expression=blt_read_plain[i] == "Success",
                                 message="Plain txt read completed with {} on BLT, LBA {}".
                                 format(blt_read_plain[i], start_count))

            md5sum_plain_read = self.linux_host.md5sum(file_name="/tmp/plain_read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=self.md5sum_input == md5sum_plain_read,
                                   message="There is a mismatch in data read after mount with encryption, input "
                                           "md5sum {}, read md5sum {} for LBA {}".
                                   format(self.md5sum_input, md5sum_plain_read, start_count))

            # Verify the output with openssl if self.write_size is 4k
            if self.write_size == 4096:
                hex_lba = hex(start_count)
                # Remove 0x
                hex_lba = hex_lba[2:]
                # LBA is denoted as 0x01 0x02
                # if len(hex_lba) == 1:
                #     hex_lba = str(0) + hex_lba
                # lba_tweak = hex_lba.ljust(16, '0') #looks like this has changed now so line 351 to 353 is not needed.
                # Its 000000000000000a not 0a00000000000000
                lba_tweak = hex_lba.rjust(16, '0')
                tweak = lba_tweak + self.xts_tweak
                # Encrypt using openssl
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=self.xts_key,
                    iv=tweak,
                    input_file="/tmp/input_file.txt",
                    output_file="/tmp/ssl_encrypted" + "_lba_" + str(start_count),
                    encrypt=True)
                fun_test.simple_assert(ssl_result, "Encrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    self.xts_key,
                                                                    tweak,
                                                                    "/tmp/ssl_encrypted" + "_lba_" + str(start_count)))

                # Decrypt encrypted LBA data
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=self.xts_key, iv=tweak,
                    input_file="/tmp/enc_read_blt" + "_lba_" + str(start_count),
                    output_file="/tmp/ssl_decrypted" + "_lba_" + str(start_count),
                    encrypt=False)
                fun_test.simple_assert(ssl_result, "Decrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    self.xts_key,
                                                                    tweak,
                                                                    "/tmp/enc_read_blt" + "_lba_" + str(start_count)))
                ssl_encrypted_md5sum = self.linux_host.md5sum(file_name="/tmp/ssl_encrypted" + "_lba_" + str(start_count))
                ssl_decrypted_md5sum = self.linux_host.md5sum(file_name="/tmp/ssl_decrypted" + "_lba_" + str(start_count))
                fun_test.test_assert(expression=ssl_encrypted_md5sum == md5sum_cipher[i],
                                     message="Compare md5sum of Encrypted file from openssl for LBA {}".
                                     format(start_count))
                fun_test.test_assert(expression=self.md5sum_input == ssl_decrypted_md5sum,
                                     message="Compare md5sum of Decrypted file from openssl for LBA {}".
                                     format(start_count))

            start_count += write_block_count
        fun_test.simple_assert(expression=len(md5sum_cipher) == len(set(md5sum_cipher)),
                               message="There seems to be same encrypted data on different LBA, {}".
                               format(md5sum_cipher))
        
    def cleanup(self):
        self.linux_host = fun_test.shared_variables["host_handle"]

        if not self.blt_creation_fail:
            if self.device_details["status"]:
                temp = self.device_details["nvme_device"].split("/")[-1]
                temp1 = re.search('nvme(.[0-9]*)', temp)
                nvme_disconnect_device = temp1.group()
                if nvme_disconnect_device:
                    self.linux_host.sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                    nvme_dev_output = fetch_nvme_list(self.linux_host)
                    if nvme_dev_output["status"]:
                        fun_test.critical(False, "NVMe disconnect failed")
                        self.linux_host.disconnect()
                    else:
                        fun_test.shared_variables["nvme_discovery"] = False
            command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                   ns_id=1,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach BLT {} from ctrlr".
                                 format(self.thin_uuid[1]))

            command_result = self.storage_controller.delete_volume(name="thin_block1",
                                                                   uuid=self.thin_uuid[1],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.test_assert(command_result["status"], "Delete BLT with uuid {}".
                                 format(self.thin_uuid[1]))

            try:
                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Delete of controller")
            except:
                fun_test.critical("Controller failed to get deleted")

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


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(BLTKey256())

    bltscript.run()
