from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from web.fun_test.analytics_models_helper import VolumePerformanceEmulationHelper, BltVolumePerformanceHelper
from lib.host.linux import Linux
from lib.host.palladium import DpcshProxy
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.f1 import F1
from lib.fun.fs import Fs
import uuid
from datetime import datetime
#from thin_block_volume_fs_perf_tuning import *

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_EMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "num_f1s": 1,
            "ip": "",
            "user": REGRESSION_USER,
            "passwd": REGRESSION_USER_PASSWORD,
            "emu_target": "",
            "model": "",
            "run_mode": "build_only",
            "pci_mode": "all",
            "bootarg": "app=mdt_test,load_mods --serial --memvol --dpc-server --dpc-uart syslog=2",
            "huid": 3,
            "ctlid": 2,
            "fnid": 2,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY,
            "perf_multiplier": 1
        },
    },
    "dpcsh_proxy": {
        "ip": "10.1.20.154",
        "user": "fun",
        "passwd": "123",
        "dpcsh_port": 40220,
        "dpcsh_tty": "/dev/ttyUSB8"
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.20.154",
            "user": "fun",
            "passwd": "123",
            "ipmi_name": "",
            "ipmi_iface": "",
            "ipmi_user": "admin",
            "ipmi_passwd": "admin",
        }
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

    memvol = BltVolumePerformanceHelper()
    memvol.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
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


class MemVolPerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.deploy()

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"], disable_f1_index=1)
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_current_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        #self.storage_controller = StorageController(target_ip=tb_config["dpcsh_proxy"]["ip"],
        #                                            target_port=tb_config["dpcsh_proxy"]["dpcsh_port"])
        self.storage_controller = f1.get_dpc_storage_controller()

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", 2], legacy=False)
        fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=2, actual=command_result["data"], message="Checking syslog level")

        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # Detach the volume and delete the controller and volume
        try:
            self.volume_details = fun_test.shared_variables["volume_details"]
            command_result = self.storage_controller.detach_volume_from_controller(ns_id=self.volume_details["ns_id"],
                                                                    ctrlr_uuid=fun_test.shared_variables["ctrlr_uuid"],
                                                                    command_duration=30)
            fun_test.test_assert(command_result["status"], "Detaching memory volume from controller on DUT")

            # Deleting the volume
            command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   type=self.volume_details["type"],
                                                                   name=self.volume_details["name"],
                                                                   uuid=fun_test.shared_variables["thin_uuid"],
                                                                   command_duration=10)
            fun_test.test_assert(command_result["status"], "Deleting memory volume on DUT")

            # Deleting the controller
            command_result = self.storage_controller.delete_controller(
                ctrlr_uuid=fun_test.shared_variables["ctrlr_uuid"],
                command_duration=10)
            fun_test.test_assert(command_result["status"], "Deleting storage controller on DUT")
        except:
            pass

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


class MemVolPerformanceTestcase(FunTestCase):
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

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

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
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        num_volume = self.num_volume
        fun_test.shared_variables["num_volume"] = num_volume

        self.nvme_block_device = self.nvme_device + "n" + str(self.volume_details["ns_id"])
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        '''self.end_host = Linux(host_ip=tb_config["tg_info"][0]["ip"],
                                  ssh_username=tb_config["tg_info"][0]["user"],
                                  ssh_password=tb_config["tg_info"][0]["passwd"])'''

        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()

        f1 = fun_test.shared_variables["f1"]

        if "memvol" not in fun_test.shared_variables or not fun_test.shared_variables["memvol"]["setup_created"]:
            fun_test.shared_variables["memvol"] = {}
            fun_test.shared_variables["memvol"]["setup_created"] = False
            fun_test.shared_variables["volume_details"] = self.volume_details

            # self.end_host.enter_sudo()
            self.end_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.end_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            # Configuring Local thin block volume
            """
            vol_size = self.volume_details["capacity"] / self.volume_details["block_size"]
            '''create_ns = self.end_host.nvme_create_namespace(size=vol_size, capacity=vol_size,
                                                            block_size=self.volume_details["block_size"],
                                                            device=self.nvme_device)'''
            create_ns = self.end_host.sudo_command(
                "nvme create-ns --nsze={} --ncap={} --block-size={} {}".format(vol_size, vol_size,
                                                                               self.volume_details["block_size"],
                                                                               self.nvme_device))
            fun_test.test_assert("Success" in create_ns, "Namespace is created")

            attach_ns = self.end_host.nvme_attach_namespace(namespace_id=self.volume_details["ns_id"],
                                                            controllers=self.controllers,
                                                            device=self.nvme_device)
            fun_test.test_assert("Success" in attach_ns, "Namespace is attached")
            # self.end_host.exit_sudo()
            """

            # Creating memory volume
            self.thin_uuid = utils.generate_uuid()
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid
            command_result = self.storage_controller.create_volume(
                        type=self.volume_details["type"],
                        capacity=self.volume_details["capacity"], block_size=self.volume_details["block_size"],
                        name=self.volume_details["name"], uuid=self.thin_uuid, command_duration=self.command_timeout)
            # command_result = self.storage_controller.create_thin_block_volume(
            #    capacity=self.volume_details["capacity"], block_size=self.volume_details["block_size"],
            #    name=self.volume_details["name"], uuid=self.thin_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Mem volume on Dut Instance 0")

            # Creating PCIe controller
            self.ctrlr_uuid = utils.generate_uuid()
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            command_result = self.storage_controller.create_controller(
                ctrlr_uuid=self.ctrlr_uuid,
                transport="PCI",
                huid=tb_config['dut_info'][0]['huid'],
                ctlid=tb_config['dut_info'][0]['ctlid'],
                fnid=tb_config['dut_info'][0]['fnid'],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                 format(self.ctrlr_uuid))

            # Attaching the volume
            command_result = self.storage_controller.attach_volume_to_controller(
                ns_id=self.volume_details["ns_id"], ctrlr_uuid=self.ctrlr_uuid, vol_uuid=self.thin_uuid,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching Mem volume on Dut Instance 0")

            # fun_test.shared_variables["memvol"]["setup_created"] = True # Moved after warm up traffic
            # fun_test.shared_variables["memvol"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["memvol"]["thin_uuid"] = self.thin_uuid

            # ns-rescan is only required if volumes are created through dpcsh commands
            # command_result = self.end_host.sudo_command("nvme ns-rescan /dev/nvme0")
            # fun_test.log("ns-rescan output is: {}".format(command_result))

            # Checking that the above created Mem volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.volume_details["ns_id"])
            lsblk_output = self.end_host.lsblk()
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))

            # Writing entire volume with data (one time task)
            if self.warm_up_traffic:
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
            fun_test.shared_variables["memvol"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        # self.storage_controller = fun_test.shared_variables["memvol"]["storage_controller"]
        # self.thin_uuid = fun_test.shared_variables["memvol"]["thin_uuid"]
        # storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"], self.thin_uuid,
        #                                             "stats")

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
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
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

                fun_test.log("Running FIO...")
                fio_job_name = "fio_" + mode + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device, rw=mode,
                                                                 bs=fio_block_size, iodepth=fio_iodepth,
                                                                 name=fio_job_name, **self.fio_cmd_args)
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
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("MEMVOL_FS", test_method, *row_data_list)


        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Memvol Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        # fun_test.test_assert(test_result, self.summary)
        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        # self.storage_controller.disconnect()
        pass


class MemVolFioSeqRead(MemVolPerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read performance of memory volume",
                              steps='''
        1. Create a memory volume on FS attached with SSD.
        2. Export (Attach) this memory volume to the Internal COMe host connected via the PCIe interface. 
        3. Run the FIO sequential read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioSeqRead, self).setup()

    def run(self):
        super(MemVolFioSeqRead, self).run()

    def cleanup(self):
        super(MemVolFioSeqRead, self).cleanup()


class MemVolFioRandRead(MemVolPerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance of memory volume",
                              steps='''
        1. Create a memory volume on FS attached with SSD.
        2. Export (Attach) this memory volume to the Internal COMe host connected via the PCIe interface. 
        3. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioRandRead, self).setup()

    def run(self):
        super(MemVolFioRandRead, self).run()

    def cleanup(self):
        super(MemVolFioRandRead, self).cleanup()


class MemVolFioSeqWrite(MemVolPerformanceTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary='Sequential Write performance of memory block volume',
                              steps='''
        1. Create a memory volume in DUT.
        2. Export (Attach) this memory volume to the EP host connected via the PCIe interface. 
        3. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioSeqWrite, self).setup()

    def run(self):
        super(MemVolFioSeqWrite, self).run()

    def cleanup(self):
        super(MemVolFioSeqWrite, self).cleanup()


class MemVolFioRandWrite(MemVolPerformanceTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary='Random Write performance of memory block volume',
                              steps='''
        1. Create a memory volume in DUT.
        2. Export (Attach) this memory volume to the EP host connected via the PCIe interface. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioRandWrite, self).setup()

    def run(self):
        super(MemVolFioRandWrite, self).run()

    def cleanup(self):
        super(MemVolFioRandWrite, self).cleanup()


class MemVolFioSeqReadWriteMix(MemVolPerformanceTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary='Sequential Read/Write (50/50) performance of memory block volume',
                              steps='''
        1. Create a memory volume in DUT.
        2. Export (Attach) this memory volume to the EP host connected via the PCIe interface. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioSeqReadWriteMix, self).setup()

    def run(self):
        super(MemVolFioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(MemVolFioSeqReadWriteMix, self).cleanup()


class MemVolFioRandReadWriteMix(MemVolPerformanceTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary='Random Read/Write (50/50) performance of memory block volume',
                              steps='''
        1. Create a memory volume in DUT.
        2. Export (Attach) this memory volume to the EP host connected via the PCIe interface. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MemVolFioRandReadWriteMix, self).setup()

    def run(self):
        super(MemVolFioRandReadWriteMix, self).run()

    def cleanup(self):
        super(MemVolFioRandReadWriteMix, self).cleanup()


if __name__ == "__main__":

    memvolscript = MemVolPerformanceScript()
    memvolscript.add_test_case(MemVolFioSeqRead())
    memvolscript.add_test_case(MemVolFioRandRead())
    memvolscript.add_test_case(MemVolFioSeqWrite())
    memvolscript.add_test_case(MemVolFioRandWrite())
    memvolscript.add_test_case(MemVolFioSeqReadWriteMix())
    memvolscript.add_test_case(MemVolFioRandReadWriteMix())
    memvolscript.run()
