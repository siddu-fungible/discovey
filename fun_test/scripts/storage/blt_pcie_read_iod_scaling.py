from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.f1 import F1
from lib.fun.fs import Fs
from storage_helper import *
from datetime import datetime
from lib.templates.storage.fio_performance_helper import FioPerfHelper
from fun_global import is_production_mode

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "bootarg": "app=mdt_test,load_mods,hw_hsu_test --serial --dpc-server --dpc-uart --csr-replay",
            "huid": 3,
            "ctlid": 2,
            "fnid": 2,
            "perf_multiplier": 1
        },
    }
}


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
    num_volume = fun_test.shared_variables["num_volume"]

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


def create_large_blt(storage_controller, blt_args, timeout):
    # peek storage
    max_capacity = 0
    select_drive_id = None
    resp = storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives", command_duration=timeout)
    fun_test.simple_assert(resp["status"], "peek storage")
    drive_info = resp["data"]
    for drive in drive_info:
        if drive_info[drive]["capacity_bytes"] > max_capacity:
            select_drive_id = drive
            max_capacity = drive_info[drive]["capacity_bytes"]
    fun_test.simple_assert(select_drive_id, message="Ensure atleast one drive is present and selected")
    blt_args["capacity"] = max_capacity
    blt_args["capacity"] = blt_args["capacity"] - blt_args["capacity"] % blt_args["block_size"]
    blt_args["drive_uuid"] = select_drive_id
    uuid = utils.generate_uuid()
    fun_test.test_assert(storage_controller.create_volume(capacity=blt_args["capacity"],
                                                          type=blt_args["type"],
                                                          block_size=blt_args["block_size"],
                                                          name=blt_args["name"],
                                                          uuid=uuid,
                                                          drive_uuid=select_drive_id,
                                                          command_duration=timeout),
                         message="Create Thin Block Vol with Size: {}, on Drive id: {}".format(blt_args["capacity"],
                                                                                               select_drive_id))
    return uuid


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
        self.storage_controller = f1.get_dpc_storage_controller()
        if not check_come_health(storage_controller=self.storage_controller):
            fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=False), "FS bootup")
            f1 = fs.get_f1(index=0)
            self.storage_controller = f1.get_dpc_storage_controller()
        fun_test.shared_variables["f1"] = f1
        fun_test.shared_variables["db_log_time"] = get_current_time()
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["sysstat_install"] = False

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # Detach the volume
        try:
            self.blt_details = fun_test.shared_variables["blt_details"]
            command_result = self.storage_controller.volume_detach_pcie(ns_id=self.blt_details["ns_id"],
                                                                        uuid=fun_test.shared_variables["thin_uuid"],
                                                                        huid=tb_config['dut_info'][0]['huid'],
                                                                        ctlid=tb_config['dut_info'][0]['ctlid'],
                                                                        fnid=tb_config['dut_info'][0]['fnid'],
                                                                        command_duration=30)
            fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

            # Deleting the volume
            command_result = self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   type=self.blt_details["type"],
                                                                   name=self.blt_details["name"],
                                                                   uuid=fun_test.shared_variables["thin_uuid"],
                                                                   command_duration=10)
            fun_test.test_assert(command_result["status"], "Deleting BLT volume on DUT")
        except:
            fun_test.log("Volume clean-up failed")

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


class BLTVolumePerformanceTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        benchmark_parsing = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

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
        elif "fio_jobs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_jobs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        num_volume = self.num_volume
        fun_test.shared_variables["num_volume"] = num_volume
        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()

        self.storage_controller = fun_test.shared_variables["storage_controller"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            self.end_host.sudo_command("dmesg -c > /dev/null")
            self.end_host.sudo_command("iptables -F")
            self.end_host.sudo_command("ip6tables -F")

            self.end_host.modprobe(module="nvme")
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

            if not fun_test.shared_variables["sysstat_install"]:
                install_sysstat = self.end_host.install_package("sysstat")
                fun_test.test_assert(install_sysstat, "Sysstat installation")
                fun_test.shared_variables["sysstat_install"] = True

            fun_test.shared_variables["thin_uuid"] = create_large_blt(self.storage_controller, self.blt_details,
                                                                      self.command_timeout)

            # Create the controller
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

            fun_test.shared_variables["blt"]["thin_uuid"] = fun_test.shared_variables["thin_uuid"]

            # Attach controller
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 vol_uuid=fun_test.shared_variables["thin_uuid"],
                                                                                 ns_id=self.blt_details["ns_id"],
                                                                                 command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                 format(fun_test.shared_variables["thin_uuid"], self.ctrlr_uuid))
            set_syslog_level(self.storage_controller, log_level=2)

            # Checking that the above created BLT volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 1)

            '''self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.blt_details["ns_id"])

            lsblk_output = self.end_host.lsblk()
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))'''

            fetch_nvme = fetch_nvme_device(self.end_host, self.blt_details["ns_id"])
            fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
            self.nvme_block_device = fetch_nvme['nvme_device']
            fun_test.shared_variables["nvme_device"] = fetch_nvme['nvme_device']

            # Writing Preconditioning the vol ezfio logic
            if self.warm_up_traffic:
                for i in xrange(2):
                    fun_test.log("Write IO to volume, this might take long time depending on fio --size provided")
                    fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "Pre-populating the volume")
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)
            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.nvme_block_device = fun_test.shared_variables["nvme_device"]
        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        row_data_dict = {}

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

        for combo in self.fio_jobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}

            for mode in self.fio_modes:

                tmp = combo.split(',')
                fio_numjobs = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')
                fio_block_size = self.fio_bs
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict["mode"] = mode
                row_data_dict["iodepth"] = fio_iodepth
                row_data_dict["num_jobs"] = fio_numjobs
                row_data_dict["block_size"] = fio_block_size
                file_size_in_gb = self.blt_details["capacity"] / 1073741824
                row_data_dict["size"] = str(file_size_in_gb) + "GB"

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                if combo == "(1, 1)":
                    fio_job_iodepth = 1
                elif combo == "(4, 1)":
                    fio_job_iodepth = 4
                elif combo == "(8, 1)":
                    fio_job_iodepth = 8
                elif combo == "(8, 2)":
                    fio_job_iodepth = 16
                elif combo == "(8, 4)":
                    fio_job_iodepth = 32
                elif combo == "(8, 8)":
                    fio_job_iodepth = 64
                elif combo == "(8, 16)":
                    fio_job_iodepth = 128
                elif combo == "(8, 32)":
                    fio_job_iodepth = 256
                self.fio_cmd_args[
                    "runtime"] = self.optimum_run_time if fio_job_iodepth in self.optimum_iodepth_list else self.default_run_time
                self.fio_cmd_args["timeout"] = self.fio_cmd_args["runtime"] + 10
                self.end_host.sudo_command("sync && echo 3 > /proc/sys/vm/drop_caches")
                fun_test.log("Running FIO...")
                # Job name will be fio_pcie_read_blt_X_iod_scaling
                fio_job_name = "fio_pcie" + "_" + mode + "_" + "blt" + "_" + str(fio_job_iodepth) + "_" + \
                               self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}

                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                                 rw=mode,
                                                                 bs=fio_block_size,
                                                                 iodepth=fio_iodepth,
                                                                 numjobs=fio_numjobs,
                                                                 name=fio_job_name,
                                                                 **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])

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
                        # if actual < (value * (1 - self.fio_pass_threshold)) and ((value - actual) > 2):
                        if compare(actual, value, self.fio_pass_threshold, ifop):
                            fio_result[combo][mode] = False
                            '''fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "FAILED", value, actual)
                            fun_test.critical("{} {} {} is not within the allowed threshold value {}".
                                              format(op, field, actual, row_data_dict[op + field][1:]))'''
                        # elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            '''fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)'''
                            fun_test.log("{} {} {} got {} than the expected value {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            '''fun_test.add_checkpoint("{} {} check {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)'''
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                if is_production_mode():
                    post_results("BLT_PCIE_IO_Scaling", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="BLT PCIe IO Scaling", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class BLTFioSeqRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read performance of BLT volume over PCIe wih different IO Depth",
                              steps='''
        1. Create a BLT volume on FS attached with SSD.
        2. Export (Attach) this BLT volume to the Internal COMe host connected via the PCIe interface. 
        3. Run FIO sequential read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


class BLTFioRandRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance of BLT volume over PCIe wih different IO Depth",
                              steps='''
        1. Create a BLT volume on FS attached with SSD.
        2. Export (Attach) this BLT volume to the Internal COMe host connected via the PCIe interface. 
        3. Run FIO random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":
    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioSeqRead())
    bltscript.add_test_case(BLTFioRandRead())
    bltscript.run()
