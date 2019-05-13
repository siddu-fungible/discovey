from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import fun_global
from lib.fun.fs import Fs
from datetime import datetime
import re
from ast import literal_eval

'''
Script to track the performance of various read write combination of Erasure Coded volume using FIO
'''

tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_EMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "disable_f1_index": 1,
            "ip": "server26",
            "user": REGRESSION_USER,
            "passwd": REGRESSION_USER_PASSWORD,
            "emu_target": "palladium",
            "model": "StorageNetwork2",
            "run_mode": "build_only",
            "pci_mode": "all",
            "bootarg": "app=mdt_test,load_mods,hw_hsu_test --serial --dis-stats --dpc-server --dpc-uart --csr-replay --useddr",
            "huid": 3,
            "ctlid": 2,
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
        "ip": "10.1.21.213",
        "user": "fun",
        "passwd": "123",
        "dpcsh_port": 40220,
        "dpcsh_tty": "/dev/ttyUSB8"
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.21.213",
            "user": "fun",
            "passwd": "123",
            "ipmi_name": "cadence-pc-5-ilo",
            "ipmi_iface": "lanplus",
            "ipmi_user": "ADMIN",
            "ipmi_passwd": "ADMIN",
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


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.deploy()

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"],
                    disable_f1_index=tb_config["dut_info"][0]["disable_f1_index"])
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = datetime.now()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", 2], legacy=False,
                                                      command_duration=5)
        fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=2, actual=command_result["data"], message="Checking syslog level")

        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):

        try:
            # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
            self.command_timeout = 30
            self.ec_coding = fun_test.shared_variables["ec_coding"]
            self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])
            if fun_test.shared_variables[self.ec_ratio]["setup_created"]:
                self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
                self.volume_types = fun_test.shared_variables[self.ec_ratio]["volume_types"]
                self.volume_capacity = fun_test.shared_variables[self.ec_ratio]["volume_capacity"]
                self.volume_block = fun_test.shared_variables[self.ec_ratio]["volume_block"]
                self.use_lsv = fun_test.shared_variables[self.ec_ratio]["use_lsv"]
                self.ns_id = fun_test.shared_variables[self.ec_ratio]["ns_id"]

                # Detaching the EC or LS volume and deleting the LS voluem based on the use_lsv flag
                if self.use_lsv:
                    # Detaching
                    detach_uid = self.uuids[self.volume_types["lsv"]]
                    command_result = self.storage_controller.volume_detach_pcie(
                        ns_id=self.ns_id, uuid=detach_uid, huid=tb_config['dut_info'][0]['huid'],
                        ctlid=tb_config['dut_info'][0]['ctlid'], command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching LS volume on DUT")

                    # Deleting the LS volume
                    command_result = self.storage_controller.delete_volume(
                        type=self.volume_types["lsv"], capacity=self.volume_capacity["lsv"],
                        block_size=self.volume_block["lsv"], name="lsv1", uuid=self.uuids[self.volume_types["lsv"]],
                        group=self.ec_coding["ndata"], jvol_uuid=self.uuids[self.volume_types["jvol"]],
                        pvol_id=self.uuids[self.volume_types["ec"]], command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting LS volume on DUT")

                    # Deleting the journal volume
                    command_result = self.storage_controller.delete_volume(
                        type=self.volume_types["jvol"], capacity=self.volume_capacity["jvol"],
                        block_size=self.volume_block["jvol"], name="jvol1", uuid=self.uuids[self.volume_types["jvol"]],
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting Journal volume on DUT")
                else:
                    detach_uid = self.uuids[self.volume_types["ec"]]
                    command_result = self.storage_controller.volume_detach_pcie(
                        ns_id=self.ns_id, uuid=detach_uid, huid=tb_config['dut_info'][0]['huid'],
                        ctlid=tb_config['dut_info'][0]['ctlid'], command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching EC volume on DUT instance")

                # Deleting the EC volume
                command_result = self.storage_controller.delete_volume(
                    type=self.volume_types["ec"], capacity=self.volume_capacity["ec"],
                    block_size=self.volume_block["ec"],
                    name="ec1", uuid=self.uuids[self.volume_types["ec"]][0], ndata=self.ec_coding["ndata"],
                    nparity=self.ec_coding["nparity"], pvol_id=self.uuids["VOL_TYPE_BLK_LOCAL_THIN"],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting EC volume on DUT")

                # Deleting all the BLT volume on which the EC volume is configured
                for vtype in sorted(self.ec_coding):
                    for i in range(self.ec_coding[vtype]):
                        if vtype == "nparity" and self.volume_types[vtype] == self.volume_types["ndata"]:
                            i += self.ec_coding["ndata"]
                        command_result = self.storage_controller.delete_volume(
                            type=self.volume_types[vtype], capacity=self.volume_capacity[vtype],
                            block_size=self.volume_block[vtype], name=vtype + str(i),
                            uuid=self.uuids[self.volume_types[vtype]][i], command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        fun_test.test_assert(command_result["status"],
                                             "Deleting {} {} BLT volume on DUT".format(i, vtype))

            self.storage_controller.disconnect()

        except Exception as ex:
            fun_test.critical(str(ex))

        fs = fun_test.shared_variables["fs"]
        fs.cleanup()


class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

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

        # fio_bs_iodepth variable is a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size
        # Checking the block size and IO depth combo list availability
        if 'fio_njobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_njobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Checking the availability of expected FIO results
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))

        # Checking the availability of expected volume level internal stats at the end of every FIO run
        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting FIO passing threshold percentage to {} for this {} testcase, because its not set in "
                         "the {} file".format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Num jobs and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_njobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volume"] = self.num_volume

        self.storage_controller = fun_test.shared_variables["storage_controller"]

        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()
        
        f1 = fun_test.shared_variables["f1"]

        fun_test.shared_variables["ec_coding"] = self.ec_coding
        self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])
        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        if self.use_lsv:
            # LS volume capacity is the ndata times of the BLT volume capacity
            self.volume_capacity["lsv"] = self.volume_capacity["ndata"] * self.ec_coding["ndata"]

            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8MB value")
            eight_mb = 1024 * 1024 * 8
            for vtype in sorted(self.ec_coding):
                tmp = self.volume_capacity[vtype] * (1 + self.lsv_pct)
                self.volume_capacity[vtype] = int(tmp + (eight_mb - (tmp % eight_mb)))

        # Setting the EC volume capacity to ndata times of ndata volume capacity
        self.volume_capacity["ec"] = self.volume_capacity["ndata"] * self.ec_coding["ndata"]

        # Adding one more block to the plex volume size to add room for super block
        for type in sorted(self.ec_coding):
            self.volume_capacity[type] = self.volume_capacity[type] + self.volume_block[type]

        if self.ec_ratio not in fun_test.shared_variables or \
                not fun_test.shared_variables[self.ec_ratio]["setup_created"]:
            fun_test.shared_variables[self.ec_ratio] = {}
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = False
            fun_test.shared_variables[self.ec_ratio]["volume_types"] = self.volume_types
            fun_test.shared_variables[self.ec_ratio]["volume_capacity"] = self.volume_capacity
            fun_test.shared_variables[self.ec_ratio]["volume_block"] = self.volume_block
            fun_test.shared_variables[self.ec_ratio]["ns_id"] = self.ns_id
            self.uuids = {}

            self.end_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.end_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            # Configuring the controller
            command_result = {}
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")

            # Configuring ndata and nparity number of BLT volumes
            for vtype in sorted(self.ec_coding):
                self.uuids[vtype] = []
                if self.volume_types[vtype] not in self.uuids:
                    self.uuids[self.volume_types[vtype]] = []
                for i in range(self.ec_coding[vtype]):
                    this_uuid = utils.generate_uuid()
                    self.uuids[vtype].append(this_uuid)
                    self.uuids[self.volume_types[vtype]].append(this_uuid)
                    command_result = self.storage_controller.create_volume(type=self.volume_types[vtype],
                                                                           capacity=self.volume_capacity[vtype],
                                                                           block_size=self.volume_block[vtype],
                                                                           name=vtype + str(i), uuid=this_uuid,
                                                                           command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create {} {} BLT volume on DUT".format(i, vtype))

            # Configuring EC volume on top of BLT volumes
            self.uuids[self.volume_types["ec"]] = []
            this_uuid = utils.generate_uuid()
            self.uuids[self.volume_types["ec"]].append(this_uuid)
            command_result = self.storage_controller.create_volume(type=self.volume_types["ec"],
                                                                   capacity=self.volume_capacity["ec"],
                                                                   block_size=self.volume_block["ec"],
                                                                   name="ec1",
                                                                   uuid=this_uuid,
                                                                   ndata=self.ec_coding["ndata"],
                                                                   nparity=self.ec_coding["nparity"],
                                                                   pvol_id=self.uuids["VOL_TYPE_BLK_LOCAL_THIN"],
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create EC volume on DUT")
            attach_uuid = this_uuid

            # Configuring Journal & LS volume based on the script config settting
            if self.use_lsv:
                fun_test.shared_variables[self.ec_ratio]["use_lsv"] = self.use_lsv
                # Configuring the Journal volume which is a mandatory one for the LSV
                self.uuids[self.volume_types["jvol"]] = utils.generate_uuid()
                command_result = self.storage_controller.create_volume(type=self.volume_types["jvol"],
                                                                       capacity=self.volume_capacity["jvol"],
                                                                       block_size=self.volume_block["jvol"],
                                                                       name="jvol1",
                                                                       uuid=self.uuids[self.volume_types["jvol"]],
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Create Journal volume on DUT")

                # Configuring the LSV
                self.uuids[self.volume_types["lsv"]] = utils.generate_uuid()
                command_result = self.storage_controller.create_volume(type=self.volume_types["lsv"],
                                                                       capacity=self.volume_capacity["lsv"],
                                                                       block_size=self.volume_block["lsv"],
                                                                       name="lsv1",
                                                                       uuid=self.uuids[self.volume_types["lsv"]],
                                                                       group=self.ec_coding["ndata"],
                                                                       jvol_uuid=self.uuids[self.volume_types["jvol"]],
                                                                       pvol_id=self.uuids[self.volume_types["ec"]],
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Create LS volume on DUT")
                attach_uuid = self.uuids[self.volume_types["lsv"]]

            # Attaching/Exporting the EC/LS volume to the external server
            command_result = {}
            command_result = self.storage_controller.volume_attach_pcie(ns_id=self.ns_id,
                                                                        uuid=attach_uuid,
                                                                        huid=tb_config['dut_info'][0]['huid'],
                                                                        ctlid=tb_config['dut_info'][0]['ctlid'],
                                                                        command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume on DUT")

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller.poke(props_tree=["params/ecvol/error_inject", 0],
                                                          legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller.peek(props_tree="params/ecvol", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),
                                          expected=0,
                                          message="Ensuring error_injection got disabled")

            # fun_test.shared_variables[self.ec_ratio]["storage_controller"] = self.storage_controller
            fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids

            lsblk_output = self.end_host.lsblk("-b")
            fun_test.simple_assert(lsblk_output, "Listing available volumes")

            # Checking that the above created BLT volume is visible to the end host
            volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(self.ns_id)
            for volume_name in lsblk_output:
                match = re.search(volume_pattern, volume_name)
                if match:
                    self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(self.ns_id)
                    self.volume_name = self.nvme_block_device.replace("/dev/", "")
                    fun_test.test_assert_expected(expected=self.volume_name,
                                                  actual=lsblk_output[volume_name]["name"],
                                                  message="NVME block device availability")
                    break
            else:
                fun_test.test_assert(False, "{} device available".format(self.volume_name))
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = True
            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name

            # Disable the udev daemon which will skew the read stats of the volume during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for service in udev_services:
                service_status = self.end_host.systemctl(service_name=service, action="stop")
                fun_test.test_assert(service_status, "Stopping {} service".format(service))

            # Executing the FIO command to warm up the system
            if self.warm_up_traffic:
                fun_test.log("Executing the FIO command to warm up the system")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if self.ec_ratio in fun_test.shared_variables or fun_test.shared_variables[self.ec_ratio]["setup_created"]:
            self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

        # self.storage_controller = fun_test.shared_variables[self.ec_ratio]["storage_controller"]

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

        volumes = []
        for vtype in sorted(self.ec_coding):
            if self.volume_types[vtype] not in volumes:
                volumes.append(self.volume_types[vtype])
        volumes.append(self.volume_types["ec"])
        if self.use_lsv and self.check_lsv_stats:
            volumes.append(self.volume_types["lsv"])

        # Check any plex needs to be induced to fail and if so do the same
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                if index < self.ec_coding["ndata"]:
                    vtype = self.volume_types["ndata"]
                else:
                    vtype = self.volume_types["nparity"]
                    if self.volume_types["ndata"] != self.volume_types["nparity"]:
                        index = index - self.ec_coding["ndata"]
                command_result = self.storage_controller.fail_volume(uuid=self.uuids[vtype][index],
                                                                     command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Inject failure to the BLT volume having the UUID "
                                                               "{}".format(self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                              message="Ensuring fault_injection got enabled")

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

        for combo in self.fio_njobs_iodepth:
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
                num_jobs, io_depth = eval(combo)
                fio_cmd_args = self.fio_cmd_args
                fio_cmd_args['numjobs'] = num_jobs
                fio_cmd_args['iodepth'] = io_depth
                fio_cmd_args['rw'] = mode
                fio_job_name = "ec_{0}_iodepth_{1}".format(mode, (num_jobs * io_depth))
                fio_cmd_args['name'] = fio_job_name

                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_cmd_args['bs']
                row_data_dict["iodepth"] = io_depth
                row_data_dict["size"] = fio_cmd_args["size"]
                row_data_dict["fio_job_name"] = fio_job_name

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_cmd_args['bs'], io_depth, self.ec_ratio))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,  **self.fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                fun_test.test_assert(fio_output[combo][mode], "Execute fio {0} only test with the block size:{1},"
                                                              "io_depth: {2}, num_jobs: {3}".
                                     format(mode, fio_cmd_args['bs'], fio_cmd_args['iodepth'], num_jobs))

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

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                row_data_dict["fio_job_name"] = fio_job_name
                for op, stats in self.expected_fio_result[mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
                        if "latency" in field:
                            ifop = "greater"
                            elseop = "lesser"
                        else:
                            ifop = "lesser"
                            elseop = "greater"
                        # if actual < (value * (1 - self.fio_pass_threshold)) and ((value - actual) > 2):
                        if compare(actual, value, self.fio_pass_threshold, ifop):
                            fio_result[combo][mode] = False
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "FAILED", value, actual)
                            fun_test.critical("{} {} {} is not within the allowed threshold value {}".
                                              format(op, field, actual, row_data_dict[op + field][1:]))
                        # elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)
                            fun_test.log("{} {} {} got {} than the expected range {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                if fun_global.is_production_mode():
                    post_results("EC Volume", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        test_result = True
        for combo in self.fio_njobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):

        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                if index < self.ec_coding["ndata"]:
                    vtype = self.volume_types["ndata"]
                else:
                    vtype = self.volume_types["nparity"]
                    if self.volume_types["ndata"] != self.volume_types["nparity"]:
                        index = index - self.ec_coding["ndata"]
                command_result = self.storage_controller.fail_volume(uuid=self.uuids[vtype][index],
                                                                     command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Disable failure from the {} volume having the UUID "
                                                               "{}".format(vtype, self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]),
                                              expected=0,
                                              message="Ensuring fault_injection got disabled")


class EC42FioSeqReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read only performance of EC volume",
                              steps="""
        1. Create 6 BLT volumes on dut instance.
        2. Create a 4:2 EC volume on top of the 6 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to the EP host connected via the PCIe interface. 
        5. Run the FIO sequential read only test(without verify) for required block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC42FioSeqReadOnly, self).setup()

    def run(self):
        super(EC42FioSeqReadOnly, self).run()

    def cleanup(self):
        super(EC42FioSeqReadOnly, self).cleanup()


class EC42FioRandReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read only performance of EC volume",
                              steps="""
        1. Create 6 BLT volumes in dut instance.
        2. Create a 4:2 EC volume on top of the 6 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to the EP host connected via the PCIe interface.
        5. Run the FIO random read only test(without verify) for required block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC42FioRandReadOnly, self).setup()

    def run(self):
        super(EC42FioRandReadOnly, self).run()

    def cleanup(self):
        super(EC42FioRandReadOnly, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42FioSeqReadOnly())
    ecscript.add_test_case(EC42FioRandReadOnly())
    ecscript.run()
