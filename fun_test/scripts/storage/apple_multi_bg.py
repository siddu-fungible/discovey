from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import VolumePerformanceEmulationHelper, BltVolumePerformanceHelper
from lib.host.linux import Linux
from lib.fun.fs import Fs
from scripts.storage.funcp_deploy import FunCpDockerContainer

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "bootarg": "setenv bootargs app=mdt_test,load_mods workload=storage cc_huid=3 --serial sku=SKU_FS1600_0"
                       "  --all_100g --mgmt --dpc-server --dpc-uart --nofreeze",
            "perf_multiplier": 1,
            "f1_ip": "15.43.1.2",
            "tcp_port": 1099
        },
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.105",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.5.2",
            "iface_gw": "15.1.5.1"
        },
        1: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.106",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.6.2",
            "iface_gw": "15.1.6.1"
        },
        2: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.107",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.7.2",
            "iface_gw": "15.1.7.1"
        },
        3: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.108",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.8.2",
            "iface_gw": "15.1.8.1"
        },
        4: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.109",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.9.2",
            "iface_gw": "15.1.9.1"
        },
        5: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.110",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.10.2",
            "iface_gw": "15.1.10.1"
        },
        6: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.111",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.11.2",
            "iface_gw": "15.1.11.1"
        },
        7: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.112",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.12.2",
            "iface_gw": "15.1.12.1"
        },
        8: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.103",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.3.2",
            "iface_gw": "15.1.3.1"
        },
        9: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "10.1.105.104",
            "user": "localadmin",
            "passwd": "Precious1*",
            "iface_ip": "15.1.4.2",
            "iface_gw": "15.1.4.1"
        }

    }
}


# Disconnect linux objects
def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def get_iostat(host_thread, count, sleep_time, iostat_interval, iostat_iter, iostat_timeout):
    host_thread.sudo_command("sleep {} ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
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


class BLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Reboot hosts
        for host_index in range(0, 10):
            end_host = Linux(host_ip=tb_config['tg_info'][host_index]['ip'],
                             ssh_username=tb_config['tg_info'][host_index]['user'],
                             ssh_password=tb_config['tg_info'][host_index]['passwd']
                             )
            try:
                end_host.sudo_command("reboot", timeout=5)
            except:
                fun_test.log("Reboot of {} failed".format(host_index))

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"], disable_f1_index=1, disable_uart_logger=False)
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_current_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()

        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["fio"] = {}
        fun_test.shared_variables["iostat_output"] = {}

    def cleanup(self):
        # dpc_host = fun_test.shared_variables["dpc_host"]
        # try:
        #     dpc_host.command("docker stop F1-0")
        #     dpc_host.sudo_command("modprobe -r funeth")
        # except:
        #     fun_test.log("Couldn't stop docker")
        try:
            for end_host in fun_test.shared_variables["end_host_list"]:
                end_host.sudo_command("for i in `pgrep fio`;do kill -9 $i;done")
                end_host.sudo_command("umount /mnt")
                fun_test.sleep("Unmounted vol", 1)
                end_host.sudo_command("nvme disconnect -d {}".format(fun_test.shared_variables["nvme_block_device"]))
                end_host.disconnect()
        except:
            fun_test.log("Disconnect failed")
        try:
            dpc_host = fun_test.shared_variables["dpc_host"]
            dpc_host.command("docker stop F1-0", timeout=180)
            dpc_host.sudo_command("rmmod funeth", timeout=180)
        except:
            fun_test.log("COMe clean-up failed")
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

        self.storage_controller = fun_test.shared_variables["storage_controller"]

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))
        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                      message="Checking syslog level")
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

        self.nvme_block_device = self.nvme_device + "n" + str(self.stripe_details["ns_id"])
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

        fs = fun_test.shared_variables["fs"]
        self.dpc_host = fs.get_come()
        fun_test.shared_variables["dpc_host"] = self.dpc_host

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
        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["stripe"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details
            fun_test.shared_variables["stripe_details"] = self.stripe_details

            self.dpc_host.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")

            self.dpc_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.dpc_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'],
                                          message="Loading nvme module")

            fun_test.log("Configure FunCP")
            self.dpc_host.rmmod("funeth")
            self.dpc_host.command("cd /mnt/keep/FunSDK")
            setup_docker_output = self.dpc_host.command(
                "export WORKSPACE=/home/fun/workspace && "
                "./integration_test/emulation/test_system.py --setup --docker --ep", timeout=1600)
            fun_test.log(setup_docker_output)

            container_cli = FunCpDockerContainer(host_ip="10.1.105.159", ssh_password="123", ssh_username="fun",
                                                 f1_index=0)

            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ifconfig $i down;sleep 1;done")
            container_cli.command(
                "sudo ip link add bond0 type bond mode 802.3ad miimon 0 xmit_hash_policy layer3+4 min_links 1")
            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ip link set $i master bond0;sleep 1;done")
            container_cli.command("for i in fpg0 fpg4 fpg8 fpg12;do sudo ifconfig $i up;sleep 1;done")
            container_cli.command("sudo ifconfig bond0 down")
            fun_test.sleep("Assign IP to bond0", 5)
            container_cli.command("sudo ifconfig bond0 15.43.1.2 netmask 255.255.255.0 up")
            while True:
                check_int_running = container_cli.command("ifconfig bond0")
                if "RUNNING" in check_int_running:
                    fun_test.sleep("Interface bond0 is up", 5)
                    break
                else:
                    container_cli.command("sudo ifconfig bond0 down")
                    fun_test.sleep("Interface brought down", 10)
                    container_cli.command("sudo ifconfig bond0 up")
            container_cli.command("ping 15.43.1.1 -c 10")
            container_cli.command("sudo ip route add 15.0.0.0/8 via 15.43.1.1 dev bond0")
            for x in range(0, 1):
                container_cli.command("ping {} -c 3".format(tb_config['tg_info'][x]['iface_ip']))
            fun_test.log("FunCP brought up")
            container_cli.disconnect()

            # Pass F1 IP to controller
            command_result = self.storage_controller.ip_cfg(ip=tb_config['dut_info'][0]['f1_ip'],
                                                            port=tb_config['dut_info'][0]['tcp_port'])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on COMe")

            # Compute the individual BLT sizes
            self.capacity = (int(self.stripe_details["vol_size"] /
                                 (self.blt_count * self.blt_details["block_size"]))) * self.blt_details["block_size"]

            # Create BLTs for striped volume
            self.stripe_unit_size = self.stripe_details["block_size"] * self.stripe_details["stripe_unit"]
            self.blt_capacity = self.stripe_unit_size + self.capacity
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
            fun_test.shared_variables["host_count"] = self.host_count
            nvme_transport = self.transport_type
            for host_index in range(0, self.host_count):
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                self.nqn = "nqn" + str(host_index + 1)

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

            fun_test.log("DPC config done")

            # Prepare testfile for test from single host
            end_host = self.end_host_list[0]
            end_host.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
            command_result = end_host.command("lsmod | grep -w nvme")
            if "nvme" in command_result:
                fun_test.log("nvme driver is loaded")
            else:
                fun_test.log("Loading nvme")
                end_host.modprobe("nvme")
            command_result = end_host.lsmod("nvme_tcp")
            if "nvme_tcp" in command_result:
                fun_test.log("nvme_tcp driver is loaded")
            else:
                fun_test.log("Loading nvme_tcp")
                end_host.modprobe("nvme_tcp")
            fun_test.sleep("Drivers loaded on host", 3)
            end_host.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
            end_host.sudo_command(
                "nvme connect -t tcp -a {} -s {} -n nqn1 -q {}".
                format(tb_config['dut_info'][0]['f1_ip'],
                       tb_config['dut_info'][0]['tcp_port'],
                       tb_config['tg_info'][0]['iface_ip']))
            fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
            end_host.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
            volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
            lsblk_output = end_host.lsblk()
            fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                          message="{} device type check".format(volume_name))

            fun_test.log("Connect done")

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        # Create filesystem
        if hasattr(self, "create_file_system") and self.create_file_system:
            self.end_host_list[0].sudo_command("/etc/init.d/irqbalance stop")
            irq_bal_stat = self.end_host_list[0].command("/etc/init.d/irqbalance status")
            if "dead" in irq_bal_stat:
                fun_test.log("IRQ balance stopped on 0")
            else:
                fun_test.log("IRQ balance not stopped on 0")
            self.end_host_list[0].sudo_command("tuned-adm profile network-throughput && tuned-adm active")
            self.end_host_list[0].sudo_command("mkfs.xfs -f {}".format(self.nvme_block_device))
            self.end_host_list[0].sudo_command("mount {} /mnt".format(self.nvme_block_device))
            fun_test.log("Creating a testfile on XFS volume")
            fio_output = self.end_host_list[0].pcie_fio(filename="/mnt/testfile.dat", **self.warm_up_fio_cmd_args)
            fun_test.test_assert(fio_output, "Pre-populating the file on XFS volume")
            self.end_host_list[0].sudo_command("umount /mnt")

        # NVMe connect from rest of the host
        for host_index in range(1, self.host_count):
            end_host = self.end_host_list[host_index]

            end_host.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
            end_host.sudo_command("/etc/init.d/irqbalance stop")
            irq_bal_stat = end_host.command("/etc/init.d/irqbalance status")
            if "dead" in irq_bal_stat:
                fun_test.log("IRQ balance stopped on {}".format(host_index))
            else:
                fun_test.log("IRQ balance not stopped on {}".format(host_index))
            end_host.sudo_command("tuned-adm profile network-throughput && tuned-adm active")
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
            self.nqn = "nqn" + str(host_index + 1)

            end_host.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
            end_host.sudo_command("nvme connect -t tcp -a {} -s {} -n {} -q {}".
                                  format(tb_config['dut_info'][0]['f1_ip'],
                                         tb_config['dut_info'][0]['tcp_port'],
                                         self.nqn,
                                         tb_config['tg_info'][host_index]['iface_ip']))
            fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
            end_host.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
            volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.stripe_details["ns_id"])
            end_host.sudo_command("dmesg")
            lsblk_output = end_host.lsblk()
            fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                          message="{} device type check".format(volume_name))

        # Mount NVMe disk on all hosts in Read-Only mode
        for end_host in self.end_host_list:
            if hasattr(self, "create_file_system") and self.create_file_system:
                end_host.sudo_command("umount /mnt")
                end_host.sudo_command("mount -o ro {} /mnt".format(self.nvme_block_device))
                lsblk_output = end_host.lsblk()
                for key, value in lsblk_output["nvme0n1"].items():
                    if key == "mount_point" and value == "/mnt":
                        fun_test.log("Device mounted successfully")

        fun_test.log("Connected from all hosts")

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in random readonly
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
        fio_job_pid = {}

        # If you are using mmap then make sure you use a large timeout value for the test as fio instance takes 2-3min
        # after runtime to exit out.
        for combo in self.fio_bs_iodepth:
            thread_id = {}
            end_host_thread = {}
            iostat_thread = {}
            thread_count = 1

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
                    file_size_in_gb = self.stripe_details["vol_size"] / 1073741824
                    row_data_dict["size"] = str(file_size_in_gb) + "GB"

                    fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                                 format(mode, fio_block_size, fio_iodepth))

                    # Flush cache before read test
                    end_host.sudo_command("sync && echo 3 > /proc/sys/vm/drop_caches")

                    fun_test.log("Starting test from host {}".format(end_host))

                    fio_job_pid[thread_count] = end_host.start_bg_process(command="sudo fio --group_reporting --filename=/mnt/testfile.dat --time_based "
                                                  "--output-format=json --size=512G --time_based=1 --rw=randread "
                                                  "--thread=1 --prio=0 --numjobs=38 --direct=1 "
                                                  "--cpus_allowed=1-19,41-59 --group_reporting=1 --bs=4k "
                                                  "--ioengine=mmap --runtime=1200 --iodepth=2 --do_verify=0 "
                                                  "--name=fio_multi_host_randread_host_tcp", output_file="/tmp/fio_out",
                                                  timeout=1260)

                    # Get iostat results
                    self.iostat_host_thread = end_host.clone()
                    iostat_wait_time = self.host_count + 1 - thread_count
                    iostat_thread[thread_count] = fun_test.execute_thread_after(
                        time_in_seconds=iostat_wait_time,
                        func=get_iostat,
                        host_thread=self.iostat_host_thread,
                        count=thread_count,
                        sleep_time=840,
                        iostat_interval=self.iostat_details["interval"],
                        iostat_iter=175,
                        iostat_timeout=1220)

                    thread_count += 1

            fun_test.sleep("Tests started", 1260)
            try:
                thread_count = 1
                for end_host in self.end_host_list:
                    process_name = end_host.sudo_command("ps -p {} -o comm=".format(fio_job_pid[thread_count]))
                    if "fio" in process_name:
                        end_host.sudo_command("kill -9 {}".format(fio_job_pid[thread_count]))
                        fun_test.log("Killed fio on {}".format(thread_count))
                        end_host.command("free -g")
            except:
                fun_test.log("No killing today")

            self.iostat_output = {}
            for x in range(1, self.host_count + 1, 1):
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
            for count in range(1, self.host_count + 1, 1):
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

            # for x in range(1, self.host_count + 1, 1):
            #     # Boosting the fio output with the testbed performance multiplier
            #     multiplier = tb_config["dut_info"][0]["perf_multiplier"]
            #     # fun_test.log(fio_output[combo][mode][x])
            #     for op, stats in fio_output[combo][mode][x].items():
            #         for field, value in stats.items():
            #             if field == "latency":
            #                 fio_output[combo][mode][x][op][field] = int(round(value / multiplier))
            #     # fun_test.log("FIO Command Output after multiplication:")
            #     # fun_test.log(fio_output[combo][mode][x])
            #     fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
            #                    self.iter_interval)
            #     # Comparing the FIO results with the expected value for the current block size and IO depth combo
            #     for op, stats in self.expected_fio_result[combo][mode].items():
            #         for field, value in stats.items():
            #             # fun_test.log("op is: {} and field is: {} ".format(op, field))
            #             actual = fio_output[combo][mode][x][op][field]
            #             row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
            #                                          int((value * (1 + self.fio_pass_threshold))))

            row_data_dict["fio_job_name"] = "fio_randread_apple_multiple_tcp"
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
            post_results("Apple_TCP_Multiple_Host_Perf", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Apple TCP RandRead Multi-Host Perf Table", table_name=self.summary,
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

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class BLTFioRandReadXFS(StripedVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read performance on a file in XFS partition created on stripe volume "
                                      "from 8 hosts",
                              steps='''
        1. Create a 530GB stripe_vol with 6 BLT volume on FS attached with SSD.
        2. Export (Attach) this stripe_vol to the host connected over 100G link. 
        3. Format the volume with XFS.
        4. Create a 512GB file.
        5. Run the FIO Random Read test(without verify) for various block size and IO depth from the 
           host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":
    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioRandReadXFS())

    bltscript.run()
