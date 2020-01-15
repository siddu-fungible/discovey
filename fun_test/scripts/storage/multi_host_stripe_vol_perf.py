from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from storage_helper import *
from collections import OrderedDict
from lib.templates.storage.storage_controller_api import *

'''
Script to track the Apple performance on a stripe volume
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def get_iostat(host_thread, count, sleep_time, iostat_interval, iostat_iter, iostat_timeout):
    host_thread.sudo_command("sleep {} ; free -g ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
                             format(sleep_time, iostat_interval, iostat_iter), timeout=iostat_timeout)
    fun_test.shared_variables["iostat_output"][count] = \
        host_thread.sudo_command("awk '/^nvme0n1/' <(cat /tmp/iostat.log) | sed 1d")
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


class StripeVolumeLevelScript(FunTestScript):
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
        fun_test.shared_variables["iostat_output"] = {}

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
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        # fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        # fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog_level"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time

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

    def cleanup(self):
        # Umount and disconnect from host
        try:
            self.final_host_ips = fun_test.shared_variables["final_host_ips"]
            for key in self.final_host_ips:
                self.host_handles[key].sudo_command("nvme disconnect -d {}".
                                                    format(fun_test.shared_variables["nvme_block_device"]))
        except:
            fun_test.log("Clean-up from host failed")


class MultiHostStripeVolumeTestCase(FunTestCase):
    def describe(self):
        pass

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

        # Setting the list of block size and IO depth combo
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Num_jobs and IO depth combo to be used for this {} testcase is not available in "
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
            self.num_ssd = 6
        if not hasattr(self, "blt_count"):
            self.blt_count = 6

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        self.syslog = fun_test.shared_variables["syslog_level"]
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "nvme_io_q" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_q"]

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips

        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = fun_test.shared_variables["num_hosts"]

        self.final_host_ips = self.host_ips[:]
        if len(self.host_ips) < self.num_hosts:
            for i in range(len(self.host_ips), self.num_hosts):
                self.final_host_ips.append(self.host_ips[len(self.host_ips) % i])
        fun_test.shared_variables["final_host_ips"] = self.final_host_ips

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # Compute the individual BLT sizes
            self.capacity = (int(self.stripe_details["vol_size"] /
                                 (self.blt_count * self.blt_details["block_size"]))) * self.blt_details["block_size"]

            # Create BLTs for striped volume
            self.stripe_unit_size = self.stripe_details["block_size"] * self.stripe_details["stripe_unit"]
            self.blt_capacity = self.stripe_unit_size + self.capacity
            if (self.blt_capacity / self.stripe_unit_size) % 2:
                fun_test.log("Num of block in BLT is not even")
                self.blt_capacity += self.stripe_unit_size

            self.thin_uuid = []
            for i in range(1, self.blt_count + 1, 1):
                cur_uuid = utils.generate_uuid()
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

            # Create Strip Volume
            self.stripe_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                                   capacity=self.stripe_details["vol_size"],
                                                                   name="stripevol1",
                                                                   uuid=self.stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))

            # Create TCP controller for each host attached to FS
            self.ctrlr_uuid = []
            fun_test.shared_variables["host_count"] = self.num_hosts
            nvme_transport = self.transport_type
            for host_index in range(0, self.num_hosts):
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                self.nqn = "nqn" + str(host_index + 1)

                # Create NVMe-OF controller
                command_result = self.storage_controller.create_controller(ctrlr_id=0,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=unicode.upper(nvme_transport),
                                                                           remote_ip=self.final_host_ips[host_index],
                                                                           subsys_nqn=self.nqn,
                                                                           host_nqn=self.final_host_ips[host_index],
                                                                           port=self.transport_port,
                                                                           command_duration=5)

                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create storage controller for TCP with uuid {} on DUT".
                                     format(cur_uuid))

                # Attach volume to NVMe-OF controller
                self.ns_id = host_index + 1
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=cur_uuid,
                                                                                     ns_id=self.ns_id,
                                                                                     vol_uuid=self.stripe_uuid)

                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attach NVMeOF controller {} to stripe vol {} over {}".
                                     format(cur_uuid, self.stripe_uuid, nvme_transport))

            host_index = 0
            for key in self.final_host_ips:
                remote_ip = key
                self.nqn = "nqn" + str(host_index + 1)

                self.host_handles[key].sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                self.host_handles[key].sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = self.host_handles[key].command("/etc/init.d/irqbalance status")
                if "dead" in irq_bal_stat:
                    fun_test.log("IRQ balance stopped on {}".format(host_index))
                else:
                    fun_test.log("IRQ balance not stopped on {}".format(host_index))
                    self.host_handles[key].sudo_command("tuned-adm profile network-throughput && tuned-adm active")

                self.host_handles[key].start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    command_result = self.host_handles[key].sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                                  self.test_network["f1_loopback_ip"],
                                                                                  self.transport_port,
                                                                                  self.nqn,
                                                                                  self.nvme_io_queues,
                                                                                  remote_ip))
                    fun_test.log(command_result)
                else:
                    command_result = self.host_handles[key].sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            str(self.transport_port),
                                                                            self.nqn,
                                                                            remote_ip))
                    fun_test.log(command_result)
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                self.host_handles[key].sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                self.host_handles[key].sudo_command("dmesg")
                lsblk_output = self.host_handles[key].lsblk()
                fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                              message="{} device type check".format(volume_name))
                host_index += 1

            # Set syslog to user specified level
            command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))
            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=5)
            fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                          message="Checking syslog level")

            before_write_eqm = {}
            before_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            # Create filesystem
            ip_key = self.final_host_ips[0]
            if hasattr(self, "create_file_system") and self.create_file_system:
                self.host_handles[ip_key].sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
                self.host_handles[ip_key].sudo_command("mount {} /mnt".format(self.nvme_block_device))
                fun_test.log("Creating a testfile on XFS volume")
                fio_output = self.host_handles[ip_key].pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
                fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
                self.host_handles[ip_key].sudo_command("umount /mnt")
                self.host_handles[ip_key].disconnect()

            after_write_eqm = {}
            after_write_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in before_write_eqm["data"].items():
                current_value = after_write_eqm["data"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    stats_delta = current_value - value
                    fun_test.log("Write test : there is a mismatch in {} : {}".format(field, stats_delta))

            # Mount NVMe disk on all hosts in Read-Only mode
            for key in self.final_host_ips:
                if hasattr(self, "create_file_system") and self.create_file_system:
                    self.host_handles[key].sudo_command("umount /mnt")
                    self.host_handles[key].sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
                    self.host_handles[key].disconnect()

            fun_test.log("Connected from all hosts")

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.num_hosts = fun_test.shared_variables["num_hosts"]

        # Going to run the FIO test for the numjobs and iodepth combo listed in fio_jobs_iodepth in random readonly
        fio_result = {}
        fio_output = {}
        internal_result = {}

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

        # If you are using mmap then make sure you use a large timeout value for the test as fio instance takes 2-3min
        # after runtime to exit out.
        for combo in self.fio_jobs_iodepth:
            thread_id = {}
            end_host_thread = {}
            iostat_thread = {}
            thread_count = 1

            # Read EQM stats
            before_read_eqm = {}
            before_read_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for key in self.final_host_ips:
                fio_result[combo] = {}
                fio_output[combo] = {}
                internal_result[combo] = {}

                end_host_thread[thread_count] = self.host_handles[key].clone()

                for mode in self.fio_modes:

                    tmp = combo.split(',')
                    fio_block_size = "4k"
                    plain_block_size = int(re.sub("\D", "", fio_block_size))
                    fio_numjobs = tmp[0].strip('() ')
                    fio_iodepth = tmp[1].strip('() ')
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True
                    row_data_dict = {}
                    row_data_dict["mode"] = mode
                    row_data_dict["block_size"] = fio_block_size
                    row_data_dict["iodepth"] = fio_iodepth
                    file_size_in_gb = self.stripe_details["vol_size"] / 1073741824
                    row_data_dict["size"] = str(file_size_in_gb) + "GB"

                    fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                                 format(mode, fio_block_size, fio_iodepth))

                    # Flush cache before read test
                    self.host_handles[key].sudo_command("sync && echo 3 > /proc/sys/vm/drop_caches")

                    # Get iostat results
                    self.iostat_host_thread = self.host_handles[key].clone()
                    iostat_wait_time = self.num_hosts + 1 - thread_count
                    iostat_thread[thread_count] = fun_test.execute_thread_after(
                        time_in_seconds=iostat_wait_time,
                        func=get_iostat,
                        host_thread=self.iostat_host_thread,
                        count=thread_count,
                        sleep_time=int(self.fio_cmd_args["runtime"] / 1.5),
                        iostat_interval=self.iostat_details["interval"],
                        iostat_iter=int(self.fio_cmd_args["runtime"] - int(self.fio_cmd_args["runtime"] / 1.5)) /
                                    self.iostat_details["interval"],
                        iostat_timeout=self.fio_cmd_args["timeout"])

                    fun_test.log("Running FIO...")
                    fio_job_name = "fio_multi_host_" + mode + "_host_" + str(thread_count) \
                                   + "_" + self.fio_job_name[mode]
                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    fio_output[combo][mode] = {}
                    if hasattr(self, "create_file_system") and self.create_file_system:
                        test_filename = "/mnt/testfile.dat"
                    else:
                        test_filename = self.nvme_block_device
                    wait_time = self.num_hosts + 1 - thread_count
                    # fun_test.log("Wait time for thread {} is {}".format(thread_count, wait_time))
                    thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                            func=fio_parser,
                                                                            arg1=end_host_thread[thread_count],
                                                                            host_index=thread_count,
                                                                            filename=test_filename,
                                                                            rw=mode,
                                                                            numjobs=fio_numjobs,
                                                                            bs=fio_block_size,
                                                                            iodepth=fio_iodepth,
                                                                            name=fio_job_name,
                                                                            **self.fio_cmd_args)
                    fun_test.sleep("Fio threadzz", seconds=1)
                    thread_count += 1

            fun_test.sleep("Fio threads started", 10)
            for x in range(1, self.num_hosts + 1, 1):
                fun_test.log("Joining fio thread {}".format(x))
                fun_test.join_thread(fun_test_thread_id=thread_id[x])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][x])
                fun_test.test_assert(fun_test.shared_variables["fio"][x], "Fio threaded test")
                fio_output[combo][mode][x] = {}
                fio_output[combo][mode][x] = fun_test.shared_variables["fio"][x]

            after_read_eqm = {}
            after_read_eqm = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in before_read_eqm["data"].items():
                current_value = after_read_eqm["data"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    stats_delta = current_value - value
                    fun_test.log("Read test : there is a mismatch in {} stat, delta : {}".format(field, stats_delta))

            self.iostat_output = {}
            for x in range(1, self.num_hosts + 1, 1):
                fun_test.join_thread(fun_test_thread_id=iostat_thread[x])
                fun_test.log("Joining iostat thread {}".format(x))
                self.iostat_output[x] = fun_test.shared_variables["iostat_output"][x].split("\n")

            total_tps = 0
            total_kbs_read = 0
            avg_tps = {}
            avg_kbs_read = {}
            non_zero = 0
            collective_tps = 0
            collective_kbs_read = 0
            for count in range(1, self.num_hosts + 1, 1):
                for x in self.iostat_output[count]:
                    dev_output = ' '.join(x.split())
                    device_name = dev_output.split(" ")[0]
                    tps = float(dev_output.split(" ")[1])
                    kbs_read = float(dev_output.split(" ")[2])
                    if tps != 0 and kbs_read != 0:
                        iostat_bs = kbs_read / tps
                        # Here we are rounding as some stats reportedly show 3.999 & 4.00032 etc
                        if round(iostat_bs) != round(plain_block_size):
                            fun_test.critical("Block size reported by iostat {} is different than {}".
                                              format(iostat_bs, plain_block_size))
                    total_tps += tps
                    total_kbs_read += kbs_read
                    non_zero += 1
                avg_tps[count] = total_tps / non_zero
                avg_kbs_read[count] = total_kbs_read / non_zero

                fun_test.log("Host {} the avg TPS is : {}".format(count, avg_tps[count]))
                fun_test.log("Host {} the avg read rate is {} KB/s".format(count, avg_kbs_read[count]))
                fun_test.log("Host {} the IO size is {} kB".format(count, avg_kbs_read[count] / avg_tps[count]))

                collective_tps += avg_tps[count]
                collective_kbs_read += avg_kbs_read[count]
            fun_test.log("The collective tps is {}".format(collective_tps))
            fun_test.log("The collective kbs is {}".format(collective_kbs_read))

            for x in range(1, self.num_hosts + 1, 1):
                # Boosting the fio output with the testbed performance multiplier
                multiplier = 1
                # fun_test.log(fio_output[combo][mode][x])
                for op, stats in fio_output[combo][mode][x].items():
                    for field, value in stats.items():
                        if field == "latency":
                            fio_output[combo][mode][x][op][field] = int(round(value / multiplier))
                # fun_test.log("FIO Command Output after multiplication:")
                # fun_test.log(fio_output[combo][mode][x])
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        # fun_test.log("op is: {} and field is: {} ".format(op, field))
                        actual = fio_output[combo][mode][x][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))

            row_data_dict["fio_job_name"] = "fio_randread_stripe_multi_host_tcp_direct"
            row_data_dict["readiops"] = int(round(collective_tps))
            row_data_dict["readbw"] = int(round(collective_kbs_read / 1000))

            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_rows.append(row_data_list)
            post_results("Stripe_multi_host_tcp_direct", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Stripe RandRead Multi-Host TCP Direct Perf Table", table_name=self.summary,
                           table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                for x in range(1, self.num_hosts + 1, 1):
                    if not fio_result[combo][mode] or not internal_result[combo][mode]:
                        test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class RandReadStripe(MultiHostStripeVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read performance on a stripe volume on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create a 530GB Stripe volume.
        2. Create a storage controller for TCP and attach above volumes to this controller
        3. From one host connect to volume and write to it
        4. Connect from all hosts after write
        5. Run the Random Read test(without verify) using libaio for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold
        ''')


if __name__ == "__main__":
    bltscript = StripeVolumeLevelScript()
    bltscript.add_test_case(RandReadStripe())
    bltscript.run()
