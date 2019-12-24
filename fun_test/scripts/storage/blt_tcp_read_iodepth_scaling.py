from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.host.linux import Linux
from lib.fun.fs import Fs
from datetime import datetime

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "bootarg": "setenv bootargs app=mdt_test,load_mods --serial sku=SKU_FS1600_0 --all_100g"
                       " --dpc-server --dpc-uart --csr-replay --nofreeze",
            "f1_ip": "29.1.1.1",
            "tcp_port": 1099,
            "perf_multiplier": 1
        },
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.23.37",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_name": "enp175s0",
            "iface_ip": "20.1.1.1",
            "iface_gw": "20.1.1.2",
            "iface_mac": "fe:dc:ba:44:66:30"
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


class BLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Rebooting host
        end_host = Linux(host_ip=tb_config["tg_info"][0]["ip"],
                         ssh_username=tb_config["tg_info"][0]["user"],
                         ssh_password=tb_config["tg_info"][0]["passwd"])
        fun_test.shared_variables["end_host_inst"] = end_host
        try:
            end_host.reboot(non_blocking=True)
            fun_test.sleep("Host is rebooted", 20)
        except:
            fun_test.log("Reboot of host failed")

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"], disable_f1_index=1)
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_data_collection_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()
        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        '''
        try:
            self.blt_details = fun_test.shared_variables["blt_details"]
            self.end_host_inst = fun_test.shared_variables["end_host_inst"]
            command_result = self.end_host_inst.sudo_command(
                "nvme disconnect -n nqn.2017-05.com.fungible:nss-uuid1 -d nvme0n1")
            fun_test.log(command_result)

            thin_uuid = fun_test.shared_variables["thin_uuid"]
            blt_count = fun_test.shared_variables["blt_count"]
            for x in range(1, blt_count + 1, 1):
                curr_uuid = thin_uuid[x-1]
                command_result = self.storage_controller.volume_detach_remote(
                    ns_id=x, uuid=curr_uuid, remote_ip=tb_config['tg_info'][0]['remote_ip'])
                if not command_result["status"]:
                    fun_test.test_assert(command_result["status"], "Detach of BLT {} with uuid {}".
                                         format(x, curr_uuid))
                command_result = self.storage_controller.delete_volume(type=self.blt_details["type"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=curr_uuid,
                                                                       command_duration=30)
                if not command_result["status"]:
                    fun_test.test_assert(command_result["status"], "Delete of BLT {} with uuid {}".
                                         format(x, curr_uuid))
        except:
            fun_test.log("Clean-up of volume failed.")
        '''
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
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Num Jobs and IO depth combo to be used for this {} testcase is not available in "
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

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "blt_count"):
            self.blt_count = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        self.nvme_block_device = self.nvme_device + "n" + str(self.blt_details["ns_id"])
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        # Setting the syslog level
        command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

        command_result = self.storage_controller.peek("params/syslog/level")
        fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                      message="Checking syslog level")

        fs = fun_test.shared_variables["fs"]
        self.end_host = fun_test.shared_variables["end_host_inst"]

        self.dpc_host = fs.get_come()

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            self.dpc_host.sudo_command("iptables -F")
            self.dpc_host.sudo_command("ip6tables -F")

            self.dpc_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.dpc_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            '''
            # Configuring Local thin block volume
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            '''

            command_result = self.storage_controller.ip_cfg(ip=tb_config['dut_info'][0]['f1_ip'])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on COMe")

            # Create BLT's
            self.thin_uuid = []
            for x in range(1, self.blt_count + 1, 1):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid.append(cur_uuid)
                command_result = self.storage_controller.create_thin_block_volume(
                    capacity=self.blt_details["capacity"],
                    block_size=self.blt_details["block_size"],
                    name="thin_block" + str(x),
                    uuid=cur_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(x, cur_uuid))

            # Create a NVMe TCP controller
            nvme_transport = self.transport_type
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(
                ctrlr_id=0,
                ctrlr_uuid=self.ctrlr_uuid,
                ctrlr_type="BLOCK",
                transport=unicode.upper(nvme_transport),
                remote_ip=tb_config['tg_info'][0]['iface_ip'],
                subsys_nqn=self.nqn,
                host_nqn=tb_config['tg_info'][0]['iface_ip'],
                port=tb_config['dut_info'][0]['tcp_port'], command_duration=5)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create storage controller for TCP with uuid {} on DUT".
                                 format(self.ctrlr_uuid))

            for x in range(1, self.blt_count + 1, 1):
                cur_uuid = self.thin_uuid[x-1]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     ns_id=x,
                                                                                     vol_uuid=cur_uuid)
                fun_test.test_assert(command_result["status"], "Attaching BLT {} with uuid {} to controller".
                                     format(x, cur_uuid))
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid

            fun_test.sleep("Waiting for host reboot to complete", 160)

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

            command_result = self.end_host.command("route | grep 29.1.1")
            if "29.1.1.0" in command_result:
                fun_test.log("IP and GW already set")
            else:
                fun_test.log("Set IP & GW")
                iface_name = tb_config['tg_info'][0]['iface_name']
                iface_ip = tb_config['tg_info'][0]['iface_ip']
                iface_gw = tb_config['tg_info'][0]['iface_gw']
                iface_mac = tb_config['tg_info'][0]['iface_mac']
                self.end_host.sudo_command("ip addr add {}/24 dev {}".format(iface_ip, iface_name))
                self.end_host.sudo_command("ip link set {} address {}".format(iface_name, iface_mac))
                self.end_host.sudo_command("ip link set {} up".format(iface_name))
                self.end_host.sudo_command("route add -net 29.1.1.0/24 gw {}".format(iface_gw))
                self.end_host.sudo_command("arp -s {} 00:de:ad:be:ef:00".format(iface_gw))

            fun_test.sleep("x86 Config done", seconds=10)
            if hasattr(self, "nvme_io_q"):
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {} -i {}".
                    format(unicode.lower(nvme_transport),
                           tb_config['dut_info'][0]['f1_ip'],
                           tb_config['dut_info'][0]['tcp_port'],
                           self.nqn,
                           self.nvme_io_q))
                fun_test.log(command_result)
            else:
                command_result = self.end_host.sudo_command(
                    "nvme connect -t {} -a {} -s {} -n {}".
                        format(unicode.lower(nvme_transport),
                               tb_config['dut_info'][0]['f1_ip'],
                               tb_config['dut_info'][0]['tcp_port'],
                               self.nqn))
                fun_test.log(command_result)

            # Checking that the above created BLT volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.blt_details["ns_id"])
            lsblk_output = self.end_host.lsblk()
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))

            self.end_host.sudo_command("dmesg | grep -i nvme")

            # Pre-conditioning the volume (one time task)
            if self.warm_up_traffic:
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
            fun_test.log("Done with setup")
            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        row_data_dict = {}

        table_data_headers = ["Num Jobs", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["num_jobs", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []
        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}

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

                fun_test.log("Running FIO {} test for blocksize : {} using num_jobs: {}, IO depth: {}".
                             format(mode, self.fio_bs, fio_numjobs, fio_iodepth))

                if int(fio_numjobs) == 1:
                    cpus_allowed = "8"
                elif int(fio_numjobs) == 4:
                    cpus_allowed = "8,9,10,11"
                elif int(fio_numjobs) >= 8:
                    cpus_allowed = "8,9,10,11,12,13,14,15,24,25,26,27,28,29,30,31"

                # Flush cache before read test
                self.end_host.sudo_command("sync")
                self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")

                # Check EQM stats before test
                # self.eqm_stats_before = {}
                # self.eqm_stats_before = self.storage_controller.peek(props_tree="stats/eqm")
                # eqm_result = False

                fun_test.log("Running FIO...")
                fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,
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

                '''
                self.eqm_stats_after = {}
                self.eqm_stats_after = self.storage_controller.peek(props_tree="stats/eqm")

                for field, value in self.eqm_stats_before["data"].items():
                    current_value = self.eqm_stats_after["data"][field]
                    if (value != current_value) and (field != "incoming BN msg valid"):
                        eqm_result = True
                        # fun_test.test_assert_expected(value, current_value, "EQM {} stat mismatch".format(field))
                        stat_delta = current_value - value
                        fun_test.critical("There is a mismatch in {} stat, delta {}".
                                          format(field, stat_delta))
                '''
                
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

                row_data_dict["fio_job_name"] = fio_job_name

            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)
            post_results("BLT_IO_Scaling", test_method, *row_data_list)

        table_name = "BLT " + unicode.upper(mode) + " Results Summary"
        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="{}".format(table_name), table_name=self.summary, table_data=table_data)
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
                              summary="Sequential Read performance on BLT volume with different IO Depth",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Seq Read test(without verify) from the 
         host with numjobs & IOdepth : (1,1),(8,1),(16,1),(16,2),(16,4) and check the performance. 
        ''')


class BLTFioRandRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance on BLT volume with different IO Depth",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Rand Read test(without verify) from the 
         host with numjobs & IOdepth : (1,1),(8,1),(16,1),(16,2),(16,4) and check the performance. 
        ''')


if __name__ == "__main__":

    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioSeqRead())
    bltscript.add_test_case(BLTFioRandRead())

    bltscript.run()
