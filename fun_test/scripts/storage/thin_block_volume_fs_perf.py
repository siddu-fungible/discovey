from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from web.fun_test.analytics_models_helper import VolumePerformanceEmulationHelper
from lib.host.linux import Linux
from lib.host.palladium import DpcshProxy
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.f1 import F1
from lib.fun.fs import Fs
from lib.fun.fs import F1InFs
import uuid

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
            "ip": "server26",
            "user": REGRESSION_USER,
            "passwd": REGRESSION_USER_PASSWORD,
            "emu_target": "palladium",
            "model": "StorageNetwork2",
            "run_mode": "build_only",
            "pci_mode": "all",
            "bootarg": "app=mdt_test,hw_hsu_test --serial --dis-stats --dpc-server --dpc-uart --csr-replay --serdesinit --syslog=2",
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
            "ipmi_user": "admin",
            "ipmi_passwd": "admin",
        }
    }
}


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, read_latency):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "read_latency"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    VolumePerformanceEmulationHelper().add_entry(date_time=fun_test.get_start_time(),
                                                 volume=volume,
                                                 test=test,
                                                 block_size=block_size,
                                                 io_depth=int(io_depth),
                                                 size=size,
                                                 operation=operation,
                                                 write_iops=write_iops,
                                                 read_iops=read_iops,
                                                 write_bw=write_bw,
                                                 read_bw=read_bw,
                                                 write_latency=write_latency,
                                                 read_latency=read_latency)

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
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.deploy()
        '''self.dpcsh_host = DpcshProxy(ip=tb_config["dpcsh_proxy"]["ip"],
                                     dpcsh_port=tb_config["dpcsh_proxy"]["dpcsh_port"],
                                     user=tb_config["dpcsh_proxy"]["user"],
                                     password=tb_config["dpcsh_proxy"]["passwd"])'''

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"])
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        # f1.get_dpc_client().json_execute(verb="peek", data="stats/vppkts", command_duration=4)

        # self.storage_controller = StorageController(target_ip=tb_config["dpcsh_proxy"]["ip"],
        #                                            target_port=tb_config["dpcsh_proxy"]["dpcsh_port"])

        # f1fs = F1InFs(index=0, fs=fs, serial_device_path="/dev/ttyS0", serial_sbp_device_path="/dev/ttyS1")
        # self.storage_controller = f1fs.get_dpc_storage_controller()
        self.storage_controller = f1.get_dpc_storage_controller()

        ''''# Start the dpcsh proxy and ensure that the funos & dpcsh proxy is started to ready to accept inputs
        status = self.dpcsh_host.start_dpcsh_proxy(dpcsh_proxy_port=tb_config["dpcsh_proxy"]["dpcsh_port"],
                                                   dpcsh_proxy_tty=tb_config["dpcsh_proxy"]["dpcsh_tty"])
        fun_test.test_assert(status, "Start dpcsh with {} in tcp proxy mode".
                             format(tb_config["dpcsh_proxy"]["dpcsh_tty"]))
        status = ""
        status = self.dpcsh_host.ensure_started(max_time=900, interval=10)
        fun_test.test_assert(status, "dpcsh proxy ready")
        self.dpcsh_host.network_controller_obj.disconnect()'''

        status = f1.get_dpc_client().json_execute(verb="peek", data="storage", command_duration=5)

        # Setting the syslog level to 2
        # status = self.storage_controller.poke("params/syslog/level 2")
        # fun_test.test_assert(status, "Setting syslog level to 2")

        # fun_test.shared_variables["dpcsh_host"] = self.dpcsh_host
        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # Detach the volume
        self.volume_details = fun_test.shared_variables["volume_details"]
        '''command_result = self.storage_controller.volume_detach_pcie(ns_id=self.volume_details["ns_id"],
                                                                    uuid=fun_test.shared_variables["thin_uuid"],
                                                                    huid=tb_config['dut_info'][0]['huid'],
                                                                    command_duration=30)
        fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

        # Deleting the volume
        command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                               block_size=self.volume_details["block_size"],
                                                               type=self.volume_details["type"],
                                                               name=self.volume_details["name"],
                                                               uuid=fun_test.shared_variables["thin_uuid"],
                                                               command_duration=10)
        fun_test.test_assert(command_result["status"], "Deleting BLT volume on DUT")'''

        '''status = self.dpcsh_host.stop_dpcsh_proxy(dpcsh_proxy_port=tb_config["dpcsh_proxy"]["dpcsh_port"],
                                                  dpcsh_proxy_tty=tb_config["dpcsh_proxy"]["dpcsh_tty"])
        fun_test.test_assert(status, "Stopped dpcsh with {} in tcp proxy mode".
                             format(tb_config["dpcsh_proxy"]["dpcsh_tty"]))'''
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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))
        # End of benchmarking json file parsing

        self.nvme_block_device = self.nvme_device + "n" + str(self.volume_details["ns_id"])
        # self.dpcsh_host = fun_test.shared_variables["dpcsh_host"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        '''self.end_host = Linux(host_ip=tb_config["tg_info"][0]["ip"],
                                  ssh_username=tb_config["tg_info"][0]["user"],
                                  ssh_password=tb_config["tg_info"][0]["passwd"])'''

        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["volume_details"] = self.volume_details

            # Configuring Local thin block volume
            '''command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                             command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT Instance 0")'''

            self.end_host.enter_sudo()
            self.end_host.modprobe(module="nvme")
            fun_test.sleep("wait after modprob is reloaded", 2)

            vol_size = self.volume_details["capacity"] / self.volume_details["block_size"]
            create_ns = self.end_host.nvme_create_namespace(size=vol_size, capacity=vol_size,
                                                            block_size=self.volume_details["block_size"],
                                                            device=self.device)
            fun_test.test_assert("Success" in create_ns, "Namespace is created")

            attach_ns = self.end_host.nvme_attach_namespace(namespace_id=self.volume_details["ns_id"],
                                                            controllers=self.controllers,
                                                            device=self.device)
            fun_test.test_assert("Success" in attach_ns, "Namespace is attached")
            # self.end_host.exit_sudo()

            command_result = {}
            self.thin_uuid = utils.generate_uuid()
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid
            '''command_result = self.storage_controller.create_thin_block_volume(
                capacity=self.volume_details["capacity"], block_size=self.volume_details["block_size"],
                name=self.volume_details["name"], uuid=self.thin_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

            command_result = {}
            command_result = self.storage_controller.volume_attach_pcie(
                ns_id=self.volume_details["ns_id"], uuid=self.thin_uuid, huid=tb_config['dut_info'][0]['huid'],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")'''

            '''create_dict = {"class": "volume",
                          "opcode": "VOL_ADMIN_OPCODE_CREATE",
                          "params": {"type": "VOL_TYPE_BLK_LOCAL_THIN", "capacity": 25769803776,
                                     "block_size": 4096, "uuid": "0000000000003011", "name": "vol-demo-1"}}
            create_vol = f1.get_dpc_client().json_execute(verb="storage", data= create_dict, command_duration=4)
            fun_test.log("create volume op is: {}".format(create_vol))

            attach_dict = {"class": "controller",
                           "opcode": "ATTACH",
                           "params": {"ctlid": 2, "huid": 3, "uuid": "0000000000003011", "nsid": 1, "fnid": 2}}
            attach_vol = f1.get_dpc_client().json_execute(verb="storage", data=attach_dict, command_duration=4)
            fun_test.log("Attach volume op is: {}".format(attach_vol))'''

            fun_test.shared_variables["blt"]["setup_created"] = True
            # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid

            # ns-rescan is only required if volumes are created through dpcsh commands
            # command_result = self.end_host.sudo_command("nvme ns-rescan /dev/nvme0")
            # fun_test.log("ns-rescan output is: {}".format(command_result))

            ''''# Rebooting the host to make the above volume accessible
            reboot_status = self.dpcsh_host.ipmi_power_cycle(host=tb_config["tg_info"][0]["ipmi_name"],
                                                             interface=tb_config["tg_info"][0]["ipmi_iface"],
                                                             user=tb_config["tg_info"][0]["ipmi_user"],
                                                             passwd=tb_config["tg_info"][0]["ipmi_passwd"],
                                                             interval=30)
            fun_test.test_assert(reboot_status, "End Host {} Rebooted".format(tb_config["tg_info"][0]["ip"]))
            host_up_status = self.end_host.is_host_up(timeout=self.command_timeout)
            fun_test.test_assert(host_up_status, "End Host {} is up".format(tb_config["tg_info"][0]["ip"]))'''

            # Checking that the above created BLT volume is visible to the end host
            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.volume_details["ns_id"])
            lsblk_output = self.end_host.lsblk()
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))

            ''''# Disable the udev daemon which will skew the read stats of the volume during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for service in udev_services:
                service_status = self.end_host.systemctl(service_name=service, action="stop")
                fun_test.test_assert(service_status, "Stopping {} service".format(service))'''

            # Writing 20GB data on volume (one time task)
            if self.warm_up_traffic:
                fun_test.log("Executing the FIO command to warm up the system")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output)
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        # self.storage_controller = fun_test.shared_variables["blt"]["storage_controller"]
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"], self.thin_uuid,
                                                     "stats")

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
                              "Write Throughput in KiB/s", "Read Throughput in KiB/s", "Write Latency in uSecs",
                              "Read Latency in uSecs"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "readlatency"]
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

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            if combo in self.expected_stats:
                expected_stats = self.expected_stats[combo]
            else:
                expected_stats = self.expected_stats

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

                ''''# Pulling the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree, command_duration=self.command_timeout)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

                # Pulling the initial stats in dictionary format
                initial_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in initial_stats[combo][mode]:
                        initial_stats[combo][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree,
                                                                          command_duration=self.command_timeout)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                                   format(props_tree))
                            initial_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree, command_duration=self.command_timeout)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                               format(props_tree))
                        initial_stats[combo][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the beginning of the test:".format(key))
                    fun_test.log(initial_stats[combo][mode][key])'''

                fun_test.log("Running FIO...")
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device, rw=mode,
                                                                 bs=fio_block_size, iodepth=fio_iodepth,
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
                        if field == "clatency":
                            fio_output[combo][mode][op][field] = int(round(value / multiplier))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Getting the volume stats after the FIO test
                '''command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree, command_duration=self.command_timeout)
                fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

                # Pulling the final stats in dictionary format
                final_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in final_stats[combo][mode]:
                        final_stats[combo][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree,
                                                                          command_duration=self.command_timeout)
                            fun_test.simple_assert(command_result["status"], "Final {} stats of DUT Instance 0".
                                                   format(props_tree))
                            final_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree, command_duration=self.command_timeout)
                        fun_test.simple_assert(command_result["status"], "Final {} stats of DUT Instance 0".
                                               format(props_tree))
                        final_stats[combo][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the end of the test:".format(key))
                    fun_test.log(final_stats[combo][mode][key])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for fkey, fvalue in final_volume_status[combo][mode].items():
                    # Not going to calculate the difference for the value stats which are not in the expected volume
                    # dictionary and also for the fault_injection attribute
                    if fkey not in expected_volume_stats[mode] or fkey == "fault_injection":
                        diff_volume_stats[combo][mode][fkey] = fvalue
                        continue
                    if fkey in initial_volume_status[combo][mode]:
                        ivalue = initial_volume_status[combo][mode][fkey]
                        diff_volume_stats[combo][mode][fkey] = fvalue - ivalue
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

                # Finding the difference between the stats before and after the test
                diff_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    diff_stats[combo][mode][key] = {}
                    for fkey, fvalue in final_stats[combo][mode][key].items():
                        ivalue = initial_stats[combo][mode][key][fkey]
                        diff_stats[combo][mode][key][fkey] = fvalue - ivalue
                    fun_test.log("Difference of {} stats before and after the test:".format(key))
                    fun_test.log(diff_stats[combo][mode][key])

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue'''

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
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

                # Comparing the internal volume stats with the expected value
                '''for ekey, evalue in expected_volume_stats[mode].items():
                    if ekey in diff_volume_stats[combo][mode]:
                        actual = diff_volume_stats[combo][mode][ekey]
                        # row_data_dict[ekey] = actual
                        if actual != evalue:
                            if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "PASSED", evalue, actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "PASSED", evalue,
                                                        actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "FAILED", evalue, actual)
                                fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                                  format(ekey, actual, evalue))
                        else:
                            fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                    "{}".format(ekey, mode, combo), "PASSED", evalue, actual)
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(ekey, actual, evalue))
                    else:
                        internal_result[combo][mode] = False
                        fun_test.critical("{} is not found in volume status".format(ekey))

                # Comparing the internal stats with the expected value
                for key, value in expected_stats[mode].items():
                    for ekey, evalue in expected_stats[mode][key].items():
                        if ekey in diff_stats[combo][mode][key]:
                            actual = diff_stats[combo][mode][key][ekey]
                            evalue_list = evalue.strip("()").split(",")
                            expected = int(evalue_list[0])
                            threshold = int(evalue_list[1])
                            if actual != expected:
                                if actual < expected:
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is less than the expected range "
                                                 "{}".format(ekey, key, actual, expected))
                                elif (actual > expected) and ((actual - expected) <= threshold):
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is within the expected range {}".
                                                 format(ekey, key, actual, expected))
                                else:
                                    internal_result[combo][mode] = False
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "FAILED", expected, actual)
                                    fun_test.critical("Final {} value of {} stats {} is not equal to the expected value"
                                                      " {}".format(ekey, key, actual, expected))
                            else:
                                fun_test.add_checkpoint(
                                    "{} check of {} stats for the {} test for the block size & IO depth combo "
                                    "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                fun_test.log("Final {} value of {} stats is equal to the expected value {}".
                                             format(ekey, key, actual, expected))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in {} stat".format(ekey, key))'''

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("BLT_EMU", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):

        self.storage_controller.disconnect()


class BLTFioSeqReadRandRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read & Random Read performance of BLT volume",
                              steps='''
        1. Create a BLT volume on FS attached with SSD.
        2. Export (Attach) this BLT volume to the Internal COMe host connected via the PCIe interface. 
        3. Run the FIO sequential read and Random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioSeqReadRandRead, self).setup()

    def run(self):
        super(BLTFioSeqReadRandRead, self).run()

    def cleanup(self):
        super(BLTFioSeqReadRandRead, self).cleanup()


class BLTFioRandWriteRandReadOnly(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary='Random Write & Read only performance of Thin Provisioned local block volume over'
                                      ' RDS',
                              steps='''
        1. Create a BLT volume in DUT.
        2. Export (Attach) this BLT volume to the EP host connected via the PCIe interface. 
        3. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioRandWriteRandReadOnly, self).setup()

    def run(self):
        super(BLTFioRandWriteRandReadOnly, self).run()

    def cleanup(self):
        super(BLTFioRandWriteRandReadOnly, self).cleanup()


class BLTFioSeqReadWriteMix(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary='Sequential 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a BLT volume in DUT.
        2. Export (Attach) this BLT volume to the EP host connected via the PCIe interface. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioSeqReadWriteMix, self).setup()

    def run(self):
        super(BLTFioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(BLTFioSeqReadWriteMix, self).cleanup()


class BLTFioRandReadWriteMix(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary='Random 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a BLT volume in DUT.
        2. Export (Attach) this BLT volume to the EP host connected via the PCIe interface. 
        3. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioRandReadWriteMix, self).setup()

    def run(self):
        super(BLTFioRandReadWriteMix, self).run()

    def cleanup(self):
        super(BLTFioRandReadWriteMix, self).cleanup()


if __name__ == "__main__":

    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioSeqReadRandRead())
    # bltscript.add_test_case(BLTFioRandWriteRandReadOnly())
    # bltscript.add_test_case(BLTFioSeqReadWriteMix())
    # bltscript.add_test_case(BLTFioRandReadWriteMix())
    bltscript.run()
