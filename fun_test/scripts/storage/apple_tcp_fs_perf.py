from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from web.fun_test.analytics_models_helper import VolumePerformanceEmulationHelper, BltVolumePerformanceHelper
from lib.host.linux import Linux
from lib.fun.fs import Fs
import storage_helper
from datetime import datetime

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "bootarg": "setenv bootargs app=mdt_test,load_mods,hw_hsu_test workload=storage --serial sku=SKU_FS1600_0 --all_100g"
                       " --dpc-server --dpc-uart --csr-replay --nofreeze",
            "perf_multiplier": 1,
            "f1_ip": "29.1.1.1",
            "tcp_port": 1099
        },
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "poc-server-01",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_name": "enp175s0",
            "iface_ip": "20.1.1.1",
            "iface_gw": "20.1.1.2",
            "iface_mac": "fe:dc:ba:44:66:30"
        },
        1: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "poc-server-02",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_name": "enp175s0",
            "iface_ip": "21.1.1.1",
            "iface_gw": "21.1.1.2",
            "iface_mac": "fe:dc:ba:44:66:31"
        }
    }
}


# Disconnect linux objects
def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    arg1.disconnect()


def get_iostat(host_thread, count, sleep_time, iostat_interval, iostat_iter):
    host_thread.sudo_command("sleep {} ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
                             format(sleep_time, iostat_interval, iostat_iter), timeout=400)
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
        fun_test.shared_variables["fio"] = {}
        fun_test.shared_variables["iostat_output"] = {}

    def cleanup(self):
        # pass
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # Detach the volume
        try:
            self.blt_details = fun_test.shared_variables["blt_details"]
            self.stripe_details = fun_test.shared_variables["stripe_details"]
            ns_id = 1
            # Detach volume from NVMe-OF controller
            for cur_uuid in fun_test.shared_variables["ctrlr_uuid"]:
                command_result = self.storage_controller.detach_volume_from_controller(
                    ns_id=self.stripe_details["ns_id"],
                    ctrlr_uuid=cur_uuid, command_duration=5)
                fun_test.test_assert(command_result["status"], "Detaching Stripe volume on DUT")
                ns_id += 1

            # Delete controller on FS
            for cur_uuid in fun_test.shared_variables["ctrlr_uuid"]:
                command_result = self.storage_controller.delete_controller(ctrlr_uuid=cur_uuid, command_result=5)
                fun_test.test_assert(command_result["status"], "Delete NVMe controller on DUT")

            # Deleting Stripe volume
            command_result = self.storage_controller.delete_volume(type=self.stripe_details["type"],
                                                                   name="stripevol1",
                                                                   uuid=fun_test.shared_variables["stripe_uuid"],
                                                                   command_duration=5)
            fun_test.test_assert(command_result["status"], "Deleting Stripe vol with uuid {} on DUT".
                                 format(fun_test.shared_variables["stripe_uuid"]))

            # Deleting the volume
            for i in range(0, fun_test.shared_variables["blt_count"], 1):
                cur_uuid = fun_test.shared_variables["thin_uuid"][i]
                x = i + 1
                command_result = self.storage_controller.delete_volume(type=self.blt_details["type"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=cur_uuid,
                                                                       command_duration=5)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(x, cur_uuid))

            # Disconnect from x86
            for end_host in fun_test.shared_variables["end_host_list"]:
                command_result = end_host.sudo_command(
                    "nvme disconnect -n nqn.2017-05.com.fungible:nss-uuid1 -d nvme0n1")
                fun_test.log(command_result)
        except:
            fun_test.log("Clean-up of volumes failed")

        try:
            # Disconnect from x86
            for end_host in fun_test.shared_variables["end_host_list"]:
                command_result = end_host.sudo_command(
                    "nvme disconnect -n nqn.2017-05.com.fungible:nss-uuid1 -d nvme0n1")
                fun_test.log(command_result)
        except:
            fun_test.log("Disconnect failed.")

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


class StripedVolumePerformanceTestcase(FunTestCase):
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
        self.dpc_host = fs.get_come()

        # Create linux objects for all end hosts
        self.end_host_list = []
        for host_index in range(0, self.host_count):
            self.end_host_list.append(
                Linux(host_ip=tb_config['tg_info'][host_index]['ip'],
                      ssh_username=tb_config['tg_info'][host_index]['user'],
                      ssh_password=tb_config['tg_info'][host_index]['passwd']
                      )
                )
        fun_test.shared_variables["end_host_list"] = self.end_host_list

        try:
            if hasattr(self, "reboot_host") and self.reboot_host:
                for end_host in self.end_host_list:
                    end_host.reboot(non_blocking=True)
                fun_test.sleep("Server rebooting", 340)
        except:
            fun_test.log("Failure during reboot of host")

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["stripe"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            self.dpc_host.sudo_command("iptables -F")
            self.dpc_host.sudo_command("ip6tables -F")

            self.dpc_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.dpc_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'],
                                          message="Loading nvme module")
            '''
            # Configuring Local thin block volume
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            '''

            # Pass F1 IP to controller
            command_result = self.storage_controller.ip_cfg(ip=tb_config['dut_info'][0]['f1_ip'])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on COMe")

            # Create BLTs for striped volume
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

            # Create TCP controller for each host attached to FS
            self.ctrlr_uuid = []
            fun_test.shared_variables["host_count"] = self.host_count
            nvme_transport = self.transport_type
            for host_index in range(0, self.host_count):
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                self.nqn = "nqn" + str(host_index+1)

                # Create NVMe-OF controller
                command_result = self.storage_controller.create_controller(
                    ctrlr_uuid=cur_uuid,
                    transport=unicode.upper(nvme_transport),
                    remote_ip=tb_config['tg_info'][host_index]['iface_ip'],
                    nqn=self.nqn,
                    port=tb_config['dut_info'][0]['tcp_port'], command_duration=5)

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

            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
            fun_test.shared_variables["stripe_uuid"] = self.stripe_uuid
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

            # Checking that the above created striped volume is visible to the end host
            for host_index in range(0, self.host_count):
                end_host = self.end_host_list[host_index]
                end_host.sudo_command("iptables -F")
                end_host.sudo_command("ip6tables -F")
                end_host.sudo_command("dmesg -c > /dev/null")
                # Load nvme and nvme_tcp modules
                command_result = end_host.command("lsmod | grep -w nvme")
                if "nvme" in command_result:
                    fun_test.log("nvme driver is loaded")
                else:
                    fun_test.log("Loading nvme")
                    end_host.modprobe("nvme")
                    end_host.modprobe("nvme_core")
                command_result = end_host.lsmod("nvme_tcp")
                if "nvme_tcp" in command_result:
                    fun_test.log("nvme_tcp driver is loaded")
                else:
                    fun_test.log("Loading nvme_tcp")
                    end_host.modprobe("nvme_tcp")
                    end_host.modprobe("nvme_fabrics")

                # Configure routes on the hosts
                command_result = end_host.command("route | grep 29.1.1")
                if "29.1.1.0" in command_result:
                    fun_test.log("IP and GW already set")
                else:
                    iface_ip = tb_config['tg_info'][host_index]['iface_ip']
                    iface_mac = tb_config['tg_info'][host_index]['iface_mac']
                    iface_gw = tb_config['tg_info'][host_index]['iface_gw']
                    iface_name = tb_config['tg_info'][host_index]['iface_name']
                    fun_test.log("Set IP & GW")
                    end_host.sudo_command("ip addr add {}/24 dev {}".format(iface_ip, iface_name))
                    end_host.sudo_command("ip link set {} address {}".format(iface_name, iface_mac))
                    end_host.sudo_command("ip link set {} up".format(iface_name))
                    end_host.sudo_command("route add -net 29.1.1.0/24 gw {}".format(iface_gw))
                    end_host.sudo_command("arp -s {} 00:de:ad:be:ef:00".format(iface_gw))
                    fun_test.sleep("Routes added on x86", 5)

                # NVME connect to volume on FS
                end_host.sudo_command("nvme connect -t {} -a {} -s {} -n {}".
                                      format(unicode.lower(nvme_transport),
                                             tb_config['dut_info'][0]['f1_ip'],
                                             tb_config['dut_info'][0]['tcp_port'],
                                             self.nqn))
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)

                # volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
                # lsblk_output = end_host.lsblk()
                # fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
                # fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                #                               message="{} device type check".format(volume_name))
                fetch_nvme_block_device = storage_helper.fetch_nvme_device(end_host, self.stripe_details["ns_id"])
                fun_test.test_assert(fetch_nvme_block_device['status'],
                                     message="Check: nvme device visible on end host")
                self.nvme_block_device = fetch_nvme_block_device["nvme_device"]
                fun_test.shared_variables['nvme_block_device'] = self.nvme_block_device

            # Pre-condition volume from 1 host (one time task)
            if not hasattr(self, "create_file_system") or not self.create_file_system:
                if self.warm_up_traffic:
                    fun_test.log("Initial Write IO to volume, this might take long time depending on size")
                    fio_output = self.end_host_list[0].pcie_fio(filename=self.nvme_block_device,
                                                                **self.warm_up_fio_cmd_args)
                    fun_test.test_assert(fio_output, "Pre-populating the volume")
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        # Create filesystem
        self.end_host_list[0].sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
        self.end_host_list[0].sudo_command("mount {} /mnt".format(self.nvme_block_device))
        fio_output = self.end_host_list[0].pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
        fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
        self.end_host_list[0].sudo_command("umount /mnt")

        # Mount NVMe disk on all hosts in Read-Only mode
        for end_host in self.end_host_list:
            if hasattr(self, "create_file_system") and self.create_file_system:
                end_host.sudo_command("umount /mnt")
                end_host.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in random readonly
        fio_result = {}
        fio_output = {}
        internal_result = {}

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
            thread_id = {}
            end_host_thread = {}
            thread_count = 1

            # Check EQM stats before test
            self.eqm_stats_before = {}
            self.eqm_stats_before = self.storage_controller.peek(props_tree="stats/eqm")

            for end_host in self.end_host_list:
                fio_result[combo] = {}
                fio_output[combo] = {}
                internal_result[combo] = {}

                end_host_thread[thread_count] = end_host.clone()

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
                    end_host.sudo_command("sync")
                    end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")
#
                    # Get iostat results
                    self.iostat_host_thread = end_host.clone()
                    iostat_thread = fun_test.execute_thread_after(time_in_seconds=1,
                                                                  func=get_iostat,
                                                                  host_thread=self.iostat_host_thread,
                                                                  count=thread_count,
                                                                  sleep_time=self.fio_cmd_args["runtime"]/4,
                                                                  iostat_interval=self.iostat_details["interval"],
                                                                  iostat_iter=self.iostat_details["iterations"] + 1)

                    fun_test.log("Running FIO...")
                    fio_job_name = "fio_" + mode + "_" + self.fio_job_name[mode]
                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    fio_output[combo][mode] = {}
                    if hasattr(self, "create_file_system") and self.create_file_system:
                        test_filename = "/mnt/testfile.dat"
                    else:
                        test_filename = self.nvme_block_device
                    wait_time = self.host_count + 1 - thread_count
                    thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                            func=fio_parser,
                                                                            arg1=end_host_thread[thread_count],
                                                                            host_index=thread_count,
                                                                            filename=test_filename,
                                                                            rw=mode,
                                                                            bs=fio_block_size,
                                                                            iodepth=fio_iodepth,
                                                                            name=fio_job_name,
                                                                            **self.fio_cmd_args)
                    fun_test.sleep("Fio threadzz", seconds=1)
                    thread_count += 1

                    # fio_output[combo][mode] = end_host.pcie_fio(filename=test_filename,
                    #                                             rw=mode,
                    #                                             bs=fio_block_size,
                    #                                             iodepth=fio_iodepth,
                    #                                             name=fio_job_name,
                    #                                             **self.fio_cmd_args)
            fun_test.sleep("Fio threads started", 10)
            for x in range(1, self.host_count + 1, 1):
                fun_test.log("Joining thread {}".format(x))
                fun_test.join_thread(fun_test_thread_id=thread_id[x])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][x])
                fun_test.test_assert(fun_test.shared_variables["fio"][x], "Fio threaded test")
                fio_output[combo][mode][x] = {}
                fio_output[combo][mode][x] = fun_test.shared_variables["fio"][x]

            # fun_test.log("FIO Command Output:")
            # fun_test.log(fio_output[combo][mode])
            # fun_test.test_assert(fio_output[combo][mode], "Fio {} test for bs {} & iodepth {}".
            #                      format(mode, fio_block_size, fio_iodepth))

            self.iostat_output = {}
            for x in range(1, self.host_count + 1, 1):
                fun_test.join_thread(fun_test_thread_id=iostat_thread)
                self.iostat_output[x] = fun_test.shared_variables["iostat_output"][x].split("\n")

            self.eqm_stats_after = {}
            self.eqm_stats_after = self.storage_controller.peek(props_tree="stats/eqm")

            for field, value in self.eqm_stats_before["data"].items():
                current_value = self.eqm_stats_after["data"][field]
                if (value != current_value) and (field != "incoming BN msg valid"):
                    # fun_test.test_assert_expected(value, current_value, "EQM {} stat mismatch".format(field))
                    stat_delta = current_value - value
                    fun_test.critical("There is a mismatch in {} stat, delta {}".
                                      format(field, stat_delta))

            for end_host in self.end_host_list:
                if hasattr(self, "create_file_system") and self.create_file_system:
                    end_host.sudo_command("umount /mnt")

            # Uncomment later
            total_tps = 0
            total_kbs_read = 0
            avg_tps = {}
            avg_kbs_read = {}
            for count in range(1, self.host_count + 1, 1):
                for x in self.iostat_output[count]:
                    dev_output = ' '.join(x.split())
                    device_name = dev_output.split(" ")[0]
                    tps = float(dev_output.split(" ")[1])
                    kbs_read = float(dev_output.split(" ")[2])
                    iostat_bs = kbs_read / tps
                    # Here we are rounding as some stats reportedly show 3.999 & 4.00032 etc
                    if round(iostat_bs) != round(plain_block_size):
                        fun_test.critical("Block size reported by iostat {} is different than {}".
                                          format(iostat_bs, plain_block_size))
                    total_tps += tps
                    total_kbs_read += kbs_read
                avg_tps[count] = total_tps / self.iostat_details["iterations"]
                avg_kbs_read[count] = total_kbs_read / self.iostat_details["iterations"]
                fun_test.log("The avg TPS is : {}".format(avg_tps[count]))
                fun_test.log("The avg read rate is {} KB/s".format(avg_kbs_read[count]))
                fun_test.log("The IO size is {} kB".format(avg_kbs_read[count]/avg_tps[count]))

            for x in range(1, self.host_count + 1, 1):
                # Boosting the fio output with the testbed performance multiplier
                multiplier = tb_config["dut_info"][0]["perf_multiplier"]
                fun_test.log(fio_output[combo][mode][x])
                for op, stats in fio_output[combo][mode][x].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][x][op][field] = int(round(value * multiplier))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][x][op][field] = int(round(value * multiplier / 1000))
                        if field == "latency":
                            fio_output[combo][mode][x][op][field] = int(round(value / multiplier))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode][x])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        fun_test.log("op is: {} and field is: {} ".format(op, field))
                        actual = fio_output[combo][mode][x][op][field]
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
                row_data_dict["readiops"] = int(round(avg_tps[x]))
                row_data_dict["readbw"] = int(round(avg_kbs_read[x] / 1000))

            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_rows.append(row_data_list)
            post_results("Apple_TCP_Perf", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Apple TCP Perf Table", table_name=self.summary,
                           table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                for x in range(1, self.host_count + 1, 1):
                    if not fio_result[combo][mode] or not internal_result[combo][mode]:
                        test_result = False

        # fun_test.test_assert(test_result, self.summary)
        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class BLTFioRandReadXFS(StripedVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read performance on a file in XFS partition created on stripe volume "
                                      "with 24 num_job & IOdepth set to 2",
                              steps='''
        1. Create a 66GB stripe_vol with 6 BLT volume on FS attached with SSD.
        2. Export (Attach) this stripe_vol to the host connected over 100G link. 
        3. Format the volume with XFS.
        4. Create a 64G file.
        5. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
           host and check the performance are inline with the expected threshold. 
        ''')


class BLTFioRandRead(StripedVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance on stripe volume "
                                      "with 24 num_job & IOdepth set to 2",
                              steps='''
        1. Create a 64G stripe_vol with 6 BLT volume on FS attached with SSD.
        2. Export (Attach) this stripe_vol to the host connected over 100G link. 
        3. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
           host and check the performance are inline with the expected threshold.  
        ''')


if __name__ == "__main__":

    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioRandReadXFS())
#    bltscript.add_test_case(BLTFioRandRead())

    bltscript.run()
