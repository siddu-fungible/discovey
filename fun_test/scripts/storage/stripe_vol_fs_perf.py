from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.fun.fs import Fs
import storage_helper
from datetime import datetime
from lib.templates.storage.fio_performance_helper import FioPerfHelper

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''

# As of now the dictionary variable containing the setup/testbed info used in this script

tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "bootarg": "app=mdt_test,load_mods --serial --dpc-server --dpc-uart --csr-replay",
            "huid": 3,
            "ctlid": 2,
            "fnid": 2,
            "perf_multiplier": 1
        }
    }
}


def get_iostat(host_thread, sleep_time, iostat_interval, iostat_iter):
    host_thread.sudo_command("sleep {} ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
                             format(sleep_time, iostat_interval, iostat_iter), timeout=400)
    host_thread.sudo_command("awk '/^nvme0n1/' <(cat /tmp/iostat.log) | sed 1d > /tmp/iostat_final.log")

    fun_test.shared_variables["avg_tps"] = host_thread.sudo_command(
        "awk '{ total += $2 } END { print total/NR }' /tmp/iostat_final.log")

    fun_test.shared_variables["avg_kbr"] = host_thread.sudo_command(
        "awk '{ total += $3 } END { print total/NR }' /tmp/iostat_final.log")

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


class BLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"], disable_f1_index=1)
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_current_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", 2], legacy=False)
        fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=2, actual=command_result["data"], message="Checking syslog level")

        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        try:
            self.blt_details = fun_test.shared_variables["blt_details"]
            self.stripe_details = fun_test.shared_variables["stripe_details"]
            command_result = self.storage_controller.volume_detach_pcie(ns_id=self.stripe_details["ns_id"],
                                                                        uuid=fun_test.shared_variables["stripe_uuid"],
                                                                        huid=tb_config['dut_info'][0]['huid'],
                                                                        ctlid=tb_config['dut_info'][0]['ctlid'],
                                                                        command_duration=30)
            fun_test.test_assert(command_result["status"], "Detaching Stripe volume on DUT")

            # Deleting Stipe volume
            command_result = self.storage_controller.delete_volume(type=self.stripe_details["type"],
                                                                   name="stripevol1",
                                                                   uuid=fun_test.shared_variables["stripe_uuid"],
                                                                   command_duration=10)
            fun_test.test_assert(command_result["status"], "Deleting Stripe vol with uuid {} on DUT".
                                 format(fun_test.shared_variables["stripe_uuid"]))

            # Deleting the volume
            for i in range(0, fun_test.shared_variables["blt_count"], 1):
                cur_uuid = fun_test.shared_variables["thin_uuid"][i]
                x = i + 1
                command_result = self.storage_controller.delete_volume(type=self.blt_details["type"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=cur_uuid,
                                                                       command_duration=10)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(x, cur_uuid))
        except:
            fun_test.log("Clean-up of volumes failed.")

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


class BLTVolumePerformanceTestcase(FunTestCase):
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
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
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
        elif "fio_bs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_bs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

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
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        blt_count = self.blt_count
        fun_test.shared_variables["blt_count"] = self.blt_count

        # self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["stripe"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            self.end_host.modprobe(module="nvme")
            self.end_host.sudo_command("iptables -F")
            self.end_host.sudo_command("ip6tables -F")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.end_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            '''
            # Configuring Local thin block volume
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            '''

            # Create BLT's
            self.stripe_unit_size = self.stripe_details["block_size"] * self.stripe_details["stripe_unit"]
            self.blt_capacity = self.stripe_unit_size + self.blt_details["capacity"]
            if ((self.blt_capacity / self.stripe_unit_size) % 2):
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
            self.stripe_vol_size = self.blt_count * self.blt_details["capacity"]
            command_result = self.storage_controller.create_volume(type=self.stripe_details["type"],
                                                                   capacity=self.stripe_vol_size,
                                                                   name="stripevol1",
                                                                   uuid=self.stripe_uuid,
                                                                   block_size=self.stripe_details["block_size"],
                                                                   stripe_unit=self.stripe_details["stripe_unit"],
                                                                   pvol_id=self.thin_uuid)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Stripe Vol with uuid {} on DUT".
                                 format(self.stripe_uuid))

            # Create controller
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(
                ctrlr_uuid=self.ctrlr_uuid,
                transport="PCI",
                fnid=tb_config['dut_info'][0]['fnid'],
                ctlid=tb_config['dut_info'][0]['ctlid'],
                huid=tb_config['dut_info'][0]['huid'],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                 format(self.ctrlr_uuid))

            # Attach controller
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 vol_uuid=self.stripe_uuid,
                                                                                 ns_id=self.stripe_details["ns_id"],
                                                                                 command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                 format(self.thin_uuid, self.ctrlr_uuid))

            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
            fun_test.shared_variables["stripe_uuid"] = self.stripe_uuid

            # Checking that the above created BLT volume is visible to the end host
            # fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            # self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
            # lsblk_output = self.end_host.lsblk()
            # fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            # fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
            #                               message="{} device type check".format(self.volume_name))
            fetch_nvme_block_device = storage_helper.fetch_nvme_device(end_host=self.end_host,
                                                                 nsid=self.stripe_details["ns_id"])
            fun_test.test_assert(fetch_nvme_block_device['status'], message="Check: nvme device visible on end host")
            self.nvme_block_device = fetch_nvme_block_device["nvme_device"]
            fun_test.shared_variables['nvme_block_device'] = self.nvme_block_device

            # Writing 20GB data on volume (one time task)
            if self.warm_up_traffic and not hasattr(self, "create_file_system"):
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                if not hasattr(self, "create_file_system"):
                    fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                    fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        if hasattr(self, "create_file_system") and self.create_file_system:
            self.end_host.sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
            self.end_host.sudo_command("mount {} /mnt".format(self.nvme_block_device))

        if hasattr(self, "create_file_system") and self.create_file_system:
            fio_output = self.end_host.pcie_fio(filename="/mnt/testfile.dat",
                                                **self.warm_up_fio_cmd_args)
            fun_test.test_assert(fio_output, "Pre-populating the testfile")
            self.end_host.sudo_command("umount /mnt")
            self.end_host.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))

        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = self.nvme_block_device

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_status = {}
        final_volume_status = {}
        diff_volume_stats = {}
        initial_stats = {}
        final_stats = {}
        diff_stats = {}

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            initial_stats[combo] = {}
            final_stats[combo] = {}
            diff_stats[combo] = {}

            for mode in self.fio_modes:

                tmp = combo.split(',')
                plain_block_size = float(tmp[0].strip('() '))
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = fio_iodepth
                row_data_dict["size"] = self.fio_cmd_args["size"]

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Flush cache before read test
                self.end_host.sudo_command("sync")
                self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")

                # Check EQM stats before test
                self.eqm_stats_before = {}
                self.eqm_stats_before = self.storage_controller.peek(props_tree="stats/eqm")

                # Get iostat results
                self.iostat_host_thread = self.end_host.clone()
                iostat_thread = fun_test.execute_thread_after(time_in_seconds=1,
                                                              func=get_iostat,
                                                              host_thread=self.iostat_host_thread,
                                                              sleep_time=self.fio_cmd_args["runtime"] / 4,
                                                              iostat_interval=self.iostat_details["interval"],
                                                              iostat_iter=(self.fio_cmd_args["runtime"] / 4) + 1)

                fun_test.log("Running FIO...")
                fio_job_name = "fio_" + mode + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=test_filename,
                                                                 rw=mode,
                                                                 bs=fio_block_size,
                                                                 iodepth=fio_iodepth,
                                                                 name=fio_job_name,
                                                                 **self.fio_cmd_args)

                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.test_assert(fio_output[combo][mode], "Fio {} test for bs {} & iodepth {}".
                                     format(mode, fio_block_size, fio_iodepth))

                fun_test.join_thread(fun_test_thread_id=iostat_thread)
                avg_tps = float(fun_test.shared_variables["avg_tps"])
                avg_kbr = float(fun_test.shared_variables["avg_kbr"])

                self.eqm_stats_after = {}
                self.eqm_stats_after = self.storage_controller.peek(props_tree="stats/eqm")

                if hasattr(self, "create_file_system") and self.create_file_system:
                    self.end_host.sudo_command("umount /mnt")

                fun_test.log("The avg TPS is : {}".format(avg_tps))
                fun_test.log("The avg read rate is {} KB/s".format(avg_kbr))
                fun_test.log("The IO size is {} kB".format(avg_kbr / avg_tps))

                for field, value in self.eqm_stats_before["data"].items():
                    current_value = self.eqm_stats_after["data"][field]
                    if (value != current_value) and (field != "incoming BN msg valid"):
                        # fun_test.test_assert_expected(value, current_value, "EQM {} stat mismatch".format(field))
                        stat_delta = current_value - value
                        fun_test.critical("There is a mismatch in {} stat, delta {}".
                                          format(field, stat_delta))

                # Boosting the fio output with the testbed performance multiplier
                multiplier = tb_config["dut_info"][0]["perf_multiplier"]
                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value * multiplier))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value * multiplier / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value / multiplier))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        fun_test.log("op is: {} and field is: {} ".format(op, field))
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
                        fun_test.log("raw_data[op + field] is: {}".format(row_data_dict[op + field]))
                        if field == "latency":
                            ifop = "greater"
                            elseop = "lesser"
                        else:
                            ifop = "lesser"
                            elseop = "greater"
                        if compare(actual, value, self.fio_pass_threshold, ifop):
                            fio_result[combo][mode] = False
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            fun_test.log("{} {} {} got {} than the expected value {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                row_data_dict["fio_job_name"] = fio_job_name
                row_data_dict["readiops"] = int(round(avg_tps))
                row_data_dict["readbw"] = int(round(avg_kbr/1000))

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("Stripe_XFS_Vol_FS", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Stripe Vol XFS Perf Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class BLTFioRandRead12XFS(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read performance on a file in XFS partition created on stripe volume "
                                      "with numjob=20 & IODepth=2",
                              steps='''
        1. Create a stripe_vol with 2 BLT volume on FS attached with SSD.
        2. Export (Attach) this stripe_vol to the Internal COMe host connected via the PCIe interface. 
        3. Format the volume with XFS.
        4. Create a 32G file.
        3. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


class BLTFioRandRead12(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance of stripe volume with 12 threads",
                              steps='''
        1. Create a stripe_vol with 2 BLT volume on FS attached with SSD.
        2. Export (Attach) this stripe_vol to the Internal COMe host connected via the PCIe interface. 
        3. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":

    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioRandRead12XFS())
    # bltscript.add_test_case(BLTFioRandRead12())

    bltscript.run()
