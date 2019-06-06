from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''

# As of now the dictionary variable containing the setup/testbed info used in this script

tb_config = {
    "name": "Storage over TCP",
    "dut_info": {
        0: {
            "bootarg": "setenv bootargs app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --serial sku=SKU_FS1600_0"
                       "  --all_100g --dis-stats --mgmt --dpc-server --dpc-uart --nofreeze",
            "perf_multiplier": 1,
            "f1_bond_ip": "15.44.1.2",
            "f1_bond_gw": "15.44.1.1",
            "f1_bond_netmask": "255.255.255.0",
            "tcp_port": 1099,
            "come_ip": "10.1.105.162"
        }
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.104",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.4.2",
            "iface_gw": "15.1.4.1"
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


class MultiBLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Rebooting host
        # end_host = Linux(host_ip=tb_config["tg_info"][0]["ip"],
        #                  ssh_username=tb_config["tg_info"][0]["user"],
        #                  ssh_password=tb_config["tg_info"][0]["passwd"])
        # fun_test.shared_variables["end_host_inst"] = end_host
        # try:
        #     end_host.reboot(non_blocking=True)
        #     fun_test.sleep("Host is rebooted", 20)
        #     # TODO: Ping and check if host is up
        # except:
        #     fun_test.log("Reboot of host failed")

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"], disable_f1_index=1, disable_uart_logger=True)
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_data_collection_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        fun_test.shared_variables["fio"] = {}

    def cleanup(self):
        try:
            self.blt_details = fun_test.shared_variables["blt_details"]

            # Deleting the volumes
            for i in range(0, fun_test.shared_variables["blt_count"], 1):
                cur_uuid = fun_test.shared_variables["thin_uuid"][i]
                command_result = self.storage_controller.volume_detach_remote(ns_id=i + 1,
                                                                            uuid=cur_uuid,
                                                                            huid=tb_config['dut_info'][0]['huid'],
                                                                            ctlid=tb_config['dut_info'][0]['ctlid'],
                                                                            command_duration=30)
                fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")
                command_result = self.storage_controller.delete_volume(type=self.blt_details["type"],
                                                                       name="thin_block" + str(i + 1),
                                                                       uuid=cur_uuid,
                                                                       command_duration=10)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(i + 1, cur_uuid))
        except:
            fun_test.log("Clean-up of volumes failed.")

        try:
            dpc_host = fun_test.shared_variables["dpc_host"]
            dpc_host.command("docker stop F1-0", timeout=180)
            dpc_host.sudo_command("rmmod funeth", timeout=180)
        except:
            fun_test.log("COMe clean-up failed")

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


class MultiBLTVolumePerformanceTestcase(FunTestCase):
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

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Numjobs and IO depth combo to be used for this {} testcase is not available in "
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
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        self.storage_controller = fun_test.shared_variables["storage_controller"]

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

        command_result = self.storage_controller.peek("params/syslog/level")
        fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                      message="Checking syslog level")

        fs = fun_test.shared_variables["fs"]
        self.dpc_host = fs.get_come()

        # Create Linux objects for end hosts
        host_index = 0
        self.end_host = Linux(host_ip=tb_config["tg_info"][host_index]["ip"],
                    ssh_username=tb_config['tg_info'][host_index]['user'],
                    ssh_password=tb_config['tg_info'][host_index]['passwd']
                    )

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            self.dpc_host.modprobe(module="nvme")
            self.dpc_host.sudo_command("iptables -F")
            self.dpc_host.sudo_command("ip6tables -F")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.dpc_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            fun_test.log("Configure FunCP")
            self.dpc_host.rmmod("funeth")
            self.dpc_host.command("cd /mnt/keep/FunSDK")
            setup_docker_output = self.dpc_host.command(
                "export WORKSPACE=/home/fun/workspace && "
                "./integration_test/emulation/test_system.py --setup --docker --ep", timeout=1600)
            fun_test.log(setup_docker_output)

            container_cli = FunCpDockerContainer(host_ip=tb_config["dut_info"][0]["come_ip"],
                                                 ssh_password="123", ssh_username="fun",
                                                 f1_index=0)

            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ifconfig $i down;sleep 1;done")
            container_cli.command(
                "sudo ip link add bond0 type bond mode 802.3ad miimon 0 xmit_hash_policy layer3+4 min_links 1")
            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ip link set $i master bond0;sleep 1;done")
            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ifconfig $i up;sleep 1;done")
            container_cli.command("sudo ifconfig bond0 down")
            fun_test.sleep("Assign IP to bond0", 5)
            container_cli.command("sudo ifconfig bond0 {} netmask {} up"
                                  "".format(tb_config["dut_info"][0]["f1_bond_ip"],
                                            tb_config["dut_info"][0]["f1_bond_netmask"]))
            while True:
                check_int_running = container_cli.command("ifconfig bond0")
                if "RUNNING" in check_int_running:
                    fun_test.sleep("Interface bond0 is up", 5)
                    break
                else:
                    container_cli.command("sudo ifconfig bond0 down")
                    fun_test.sleep("Interface brought down", 10)
                    container_cli.command("sudo ifconfig bond0 up")
            container_cli.command("ping {} -c 10".format(tb_config["dut_info"][0]["f1_bond_ip"]))
            container_cli.command("sudo ip route add 15.0.0.0/8 via {} dev bond0"
                                  "".format(tb_config["dut_info"][0]["f1_bond_gw"]))
            container_cli.command("ping {} -c 10".format(tb_config['tg_info'][host_index]['iface_ip']))
            fun_test.log("FunCP brought up")

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=tb_config['dut_info'][0]['f1_bond_ip'],
                                                            port=tb_config['dut_info'][0]['tcp_port'])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on COMe")

            # Create BLT's
            self.nvme_block_device = []
            self.thin_uuid_list = []
            for i in range(0, self.blt_count, 1):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_details["capacity"],
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(i + 1),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i + 1, cur_uuid))
                self.nvme_block_device.append(self.nvme_device + "n" + str(i + 1))
            fun_test.shared_variables["nvme_block_device_list"] = self.nvme_block_device
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

            # Create TCP controller
            nvme_transport = self.transport_type
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(
                ctrlr_uuid=self.ctrlr_uuid,
                transport=unicode.upper(nvme_transport),
                remote_ip=tb_config['tg_info'][0]['iface_ip'],
                nqn=self.nqn,
                port=tb_config['dut_info'][0]['tcp_port'],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating controller For TCP with uuid {} on DUT".
                                 format(self.ctrlr_uuid))

            # Attach controller to all BLTs
            for i in range(0, self.blt_count, 1):
                vol_uuid = fun_test.shared_variables["thin_uuid"][i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 vol_uuid=vol_uuid,
                                                                                 ns_id=i + 1,
                                                                                 command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                 format(vol_uuid, self.ctrlr_uuid))

            self.end_host.sudo_command("iptables -F")
            self.end_host.sudo_command("ip6tables -F")
            self.end_host.sudo_command("dmesg -c > /dev/null")

            try:
                self.end_host.sudo_command("service irqbalance stop")
                fun_test.sleep("Disable irqbalance", 5)
                command_result = self.end_host.sudo_command("service irqbalance status")
                if "inactive" in command_result:
                    fun_test.log("IRQ balance disabled")
                else:
                    fun_test.critical("IRQ Balance still active")
            except:
                fun_test.log("irqbalance service not found")

            install_status = self.end_host.install_package("tuned")
            fun_test.test_assert(install_status, "tuned installed successfully")

            active_profile = self.end_host.sudo_command("tuned-adm active")
            if "network-throughput" not in active_profile:
                self.end_host.sudo_command("tuned-adm profile network-throughput")

            command_result = self.end_host.command("lsmod | grep -w nvme")
            if "nvme" in command_result:
                fun_test.log("nvme driver is loaded")
            else:
                fun_test.log("Loading nvme")
                self.end_host.modprobe("nvme")
                self.end_host.modprobe("nvme_core")
            command_result = self.end_host.lsmod("nvme_tcp")
            if "nvme_tcp" in command_result:
                fun_test.log("nvme_tcp driver is loaded")
            else:
                fun_test.log("Loading nvme_tcp")
                self.end_host.modprobe("nvme_tcp")
                self.end_host.modprobe("nvme_fabrics")

            fun_test.sleep("x86 Config done", seconds=10)
            if hasattr(self, "nvme_io_q"):
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".
                        format(unicode.lower(nvme_transport),
                               tb_config['dut_info'][0]['f1_bond_ip'],
                               tb_config['dut_info'][0]['tcp_port'],
                               self.nqn,
                               self.nvme_io_q,
                               tb_config['tg_info'][0]['iface_ip']))
                fun_test.log(command_result)
            else:
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -q {}".
                        format(unicode.lower(nvme_transport),
                               tb_config['dut_info'][0]['f1_bond_ip'],
                               tb_config['dut_info'][0]['tcp_port'],
                               self.nqn,
                               tb_config['tg_info'][0]['iface_ip']))
                fun_test.log(command_result)

            # Checking that the above created BLT volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            for i in range(0, self.blt_count, 1):
                self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(i + 1)
                lsblk_output = self.end_host.lsblk()
                fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                                message="{} device type check".format(self.volume_name))

            # Pre-conditioning the volume (one time task)
            self.nvme_block_device_str = ':'.join(self.nvme_block_device)
            fun_test.shared_variables["nvme_block_device_str"] = self.nvme_block_device_str
            if self.warm_up_traffic:
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                if not hasattr(self, "create_file_system"):
                    fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device_str, **self.warm_up_fio_cmd_args)
                    fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
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
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        for combo in self.fio_jobs_iodepth:
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
                fio_block_size = self.fio_bs
                fio_numjobs = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                row_data_dict["num_jobs"] = fio_numjobs
                file_size_in_gb = self.blt_details["capacity"] / 1073741824
                row_data_dict["size"] = str(file_size_in_gb) + "GB"

                fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                             format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                if int(fio_numjobs) == 1:
                    cpus_allowed = "1"
                elif int(fio_numjobs) == 4:
                    cpus_allowed = "1-4"
                elif int(fio_numjobs) >= 8:
                    cpus_allowed = "1-19,40-59"

                # Flush cache before read test
                self.end_host.sudo_command("sync")
                self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")

                """
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
                """

                fun_test.log("Running FIO...")
                fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=fun_test.shared_variables["nvme_block_device_str"],
                                                                 numjobs=fio_numjobs,
                                                                 rw=mode,
                                                                 bs=fio_block_size,
                                                                 iodepth=fio_iodepth,
                                                                 name=fio_job_name,
                                                                 cpus_allowed=cpus_allowed,
                                                                 **self.fio_cmd_args)

                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.test_assert(fio_output[combo][mode], "Fio {} test for numjobs {} & iodepth {}".
                                     format(mode, fio_numjobs, fio_iodepth))

                """
                self.eqm_stats_after = {}
                self.eqm_stats_after = self.storage_controller.peek(props_tree="stats/eqm")
                
                for field, value in self.eqm_stats_before["data"].items():
                    current_value = self.eqm_stats_after["data"][field]
                    if (value != current_value) and (field != "incoming BN msg valid"):
                        # fun_test.test_assert_expected(value, current_value, "EQM {} stat mismatch".format(field))
                        stat_delta = current_value - value
                        fun_test.critical("There is a mismatch in {} stat, delta {}".
                                          format(field, stat_delta))
                """

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
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = actual
                        fun_test.log("raw_data[op + field] is: {}".format(row_data_dict[op + field]))

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("Multi_vol_TCP", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Multiple Volumes over TCP Perf Table", table_name=self.summary, table_data=table_data)

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

class MultiBLTFioRead12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 12 BLT volumes on F1 attached with 12 SSD
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Sequential Read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

class MultiBLTFioRandRead12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size of 4K",
                              steps='''
        1. Create 12 BLT volumes on FS attached with 12 SSD
        2. Create a storage controller for TCP and attach above volume to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

class MultiBLTFioWrite12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Sequential Read performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size of 4K",
                              steps='''
        1. Create 12 BLT volumes on FS attached with 12 SSD
        2. Create a storage controller for TCP and attach above volume to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Sequential Read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

class MultiBLTFioRandWrite12(MultiBLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Random Write performance for 12 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size of 4K",
                              steps='''
        1. Create 12 BLT volumes on FS attached with 12 SSD
        2. Create a storage controller for TCP and attach above volume to this controller
        3. Connect to this volume from remote host
        4. Run the FIO Random Write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":

    bltscript = MultiBLTVolumePerformanceScript()
    bltscript.add_test_case(MultiBLTFioRandRead12())
    bltscript.add_test_case(MultiBLTFioRandWrite12())
    bltscript.run()