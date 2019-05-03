from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.fs import Fs
from datetime import datetime
import re
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController

'''
Script to test single drive failure scenarios for 4:2 EC config
'''

class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        script_config = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in script_config or not script_config["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 2
            self.command_timeout = 5
            self.retries = 24
        else:
            for k, v in script_config["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        """NewChange
        topology_helper = TopologyHelper()
        fun_test.log("topology_helper output is: {}".format(topology_helper))
        fun_test.log("Setting dut params")
        topology_helper.set_dut_parameters(dut_index=self.f1_in_use, custom_boot_args=self.bootargs)
        fun_test.log("Started topology deploy")
        topology = topology_helper.deploy()
        fun_test.log("topology output is: {}".format(topology))
        fun_test.test_assert(topology, "Topology deployed")

        fs = topology.get_dut_instance(index=self.f1_in_use)
        fun_test.shared_variables["fs"] = fs
        NewChange"""

        # Pulling the testbed type and its config
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        fun_test.log("Testbed-type: {}".format(self.testbed_type))
        self.fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.testbed_type)
        self.testbed_config = fun_test.get_asset_manager().get_test_bed_spec(self.testbed_type)
        fun_test.log("{} FS Spec: {}".format(self.testbed_type, self.fs_spec))
        fun_test.simple_assert(self.fs_spec, "FS Spec for {}".format(self.testbed_type))

        # Getting the first network host
        for interface in self.testbed_config["dut_info"][str(self.f1_in_use)]["fpg_interface_info"]:
            if "host_info" in self.testbed_config[str(self.f1_in_use)]["fpg_interface_info"][interface]:
                self.nw_hostname = \
                    self.testbed_config[str(self.f1_in_use)]["fpg_interface_info"][interface]["host_info"]["name"]
                break

        self.host_config = fun_test.get_asset_manager().get_test_bed_spec(self.nw_hostname)

        fun_test.shared_variables["testbed_type"] = self.testbed_type
        fun_test.shared_variables["fs_spec"] = self.fs_spec
        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["host_config"] = self.host_config
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["attach"] = self.attach
        fun_test.shared_variables["test_network"] = self.test_network

        # Initializing the FS
        fs = Fs.get(boot_args=self.bootargs, disable_f1_index=self.disable_f1_index)
        fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=True), "FS bootup")

        f1 = fs.get_f1(index=self.f1_in_use)
        fun_test.shared_variables["fs"] = fs
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = datetime.now()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        # Initializing the Network attached host
        end_host_ip = self.host_config["host_ip"]
        end_host_user = self.host_config["ssh_username"]
        end_host_passwd = self.host_config["ssh_password"]

        """NewChange
        fun_test.log("End host object formation")
        self.end_host = topology.get_host_instance(dut_index=0, host_index=0, fpg_interface_index=0)
        fun_test.log(self.end_host, "Host instance on fpg interface 0: {}".format(str(self.end_host)))
        fun_test.log("end host object is created")
        end_host_ip = self.end_host.host_ip
        fun_test.log("host_ip is: {}".format(end_host_ip)) NewChange"""

        self.end_host = Linux(host_ip=end_host_ip, ssh_username=end_host_user, ssh_password=end_host_passwd)
        fun_test.shared_variables["end_host"] = self.end_host

        host_up_status = self.end_host.reboot(timeout=self.command_timeout, retries=self.retries)
        fun_test.test_assert(host_up_status, "End Host {} is up".format(end_host_ip))

        interface_ip_config = "ip addr add {} dev {}".format(self.test_network["test_interface_ip"],
                                                             self.host_config["test_interface_name"])
        interface_mac_config= "ip link set {} address {}".format(self.host_config["test_interface_name"],
                                                                 self.test_network["test_interface_mac"])
        link_up_cmd = "ip link set {} up".format(self.host_config["test_interface_name"])
        static_arp_cmd = "arp -s {} {}".format(self.test_network["test_net_route"]["gw"],
                                               self.test_network["test_net_route"]["arp"])

        interface_ip_config_status = self.end_host.sudo_command(command=interface_ip_config,
                                                                timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Configuring test interface IP address")

        interface_mac_status = self.end_host.sudo_command(command=interface_mac_config,
                                                          timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Assigning MAC to test interface")

        link_up_status = self.end_host.sudo_command(command=link_up_cmd, timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Bringing up test link")

        interface_up_status = self.end_host.ifconfig_up_down(interface=self.host_config["test_interface_name"],
                                                             action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        route_add_status = self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                                      gateway=self.test_network["test_net_route"]["gw"],
                                                      outbound_interface=self.host_config["test_interface_name"],
                                                      timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Adding route to F1")

        arp_add_status = self.end_host.sudo_command(command=static_arp_cmd, timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Adding static ARP to F1 route")

        # Loading the nvme and nvme_tcp modules
        self.end_host.modprobe(module="nvme")
        fun_test.sleep("Loading nvme module", 2)
        command_result = self.end_host.lsmod(module="nvme")
        fun_test.simple_assert(command_result, "Loading nvme module")
        fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

        self.end_host.modprobe(module="nvme_tcp")
        fun_test.sleep("Loading nvme_tcp module", 2)
        command_result = self.end_host.lsmod(module="nvme_tcp")
        fun_test.simple_assert(command_result, "Loading nvme_tcp module")
        fun_test.test_assert_expected(expected="nvme_tcp", actual=command_result['name'],
                                      message="Loading nvme_tcp module")

        self.storage_controller = f1.get_dpc_storage_controller()
        """NewChange
        self.come = fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip, target_port=self.come.get_dpc_port(0))
        NewChange"""
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Setting the syslog level
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                      legacy=False, command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=self.command_timeout)
        fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                      message="Checking syslog level")

    def cleanup(self):

        self.ec_info = fun_test.shared_variables["ec_info"]
        self.remote_ip = fun_test.shared_variables["remote_ip"]
        if fun_test.shared_variables["ec"]["setup_created"]:
            # Detaching all the EC/LS volumes to the external server
            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.volume_detach_remote(
                    ns_id=num + 1, uuid=self.ec_info["attach_uuid"][num], huid=self.attach['huid'],
                    ctlid=self.attach['ctlid'], remote_ip=self.remote_ip, transport=self.attach['transport'],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

            # Unconfiguring all the LSV/EC and it's plex volumes
            self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info, command_timeout=self.command_timeout)

        self.storage_controller.disconnect()
        fs = fun_test.shared_variables["fs"]
        fun_test.sleep("Allowing buffer time before calling fs clean-up", 60)
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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        # End of benchmarking json file parsing

        self.fs = fun_test.shared_variables["fs"]
        self.f1 = fun_test.shared_variables["f1"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.end_host = fun_test.shared_variables["end_host"]

        self.test_bed_type = fun_test.shared_variables["test_bed_type"]
        self.test_bed_spec = fun_test.shared_variables["test_bed_spec"]
        self.test_bed_config = fun_test.shared_variables["test_bed_config"]
        self.host_config = fun_test.shared_variables["host_config"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        fun_test.shared_variables["attach_transport"] = self.attach_transport
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd

        # self.nvme_block_device = self.nvme_device + "n" + str(self.ns_id)
        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        fun_test.shared_variables["ec_info"] = self.ec_info
        fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

        # Configuring the controller
        command_result = {}
        command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                         command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

        command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

        (ec_config_status, self.ec_info) = configure_ec_volume(self.storage_controller, self.ec_info,
                                                               self.command_timeout)
        fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

        fun_test.log("EC details after configuring EC Volume:")
        for k, v in self.ec_info.items():
            fun_test.log("{}: {}".format(k, v))

        # Attaching/Exporting all the EC/LS volumes to the external server
        self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip

        for num in xrange(self.ec_info["num_volumes"]):
            command_result = self.storage_controller.volume_attach_remote(
                ns_id=num+1, uuid=self.ec_info["attach_uuid"][num], huid=tb_config['dut_info'][0]['huid'],
                ctlid=tb_config['dut_info'][0]['ctlid'], remote_ip=self.remote_ip,
                transport=self.attach_transport, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

        # disabling the error_injection for the EC volume
        command_result = {}
        command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                      command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
        command_result = {}
        command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")

        # Checking nvme-connect status
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                             self.test_network["f1_loopback_ip"],
                                                                             str(self.transport_port),
                                                                             self.nvme_subsystem)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                self.attach_transport.lower(), self.test_network["f1_loopback_ip"], str(self.transport_port),
                self.nvme_subsystem, str(self.io_queues))

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        ''''# Checking that the above created volume is visible to the end host
        self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.ns_id)
        lsblk_output = self.end_host.lsblk()
        fun_test.log("lsblk output is: {}".format(lsblk_output))
        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                      message="{} device type check".format(self.volume_name))'''

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
                                              message="{} device available".format(self.volume_name))
                break
        else:
            fun_test.test_assert(False, "{} device available".format(self.volume_name))

        fun_test.shared_variables["ec"]["setup_created"] = True
        fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
        fun_test.shared_variables["volume_name"] = self.volume_name

        ''''# Disable the udev daemon which will skew the read stats of the volume during the test
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.end_host.systemctl(service_name=service, action="stop")
            fun_test.test_assert(service_status, "Stopping {} service".format(service))'''

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

        fun_test.sleep("Interval before starting traffic", self.iter_interval)
        fun_test.log("Starting Random Read/Write of 8k data block")
        self.end_host = fun_test.shared_variables["end_host"]

        fun_test.log("Building the volume performance run config file")
        self.perf_run_profile = "{}/{}".format(self.vdbench_path, self.perf_run_config_file)
        self.end_host.create_file(file_name=self.perf_run_profile, contents=self.perf_run_vdb_config)

        fun_test.log("Starting Vdbench performance run all the volumes")
        vdbench_result = self.end_host.vdbench(path=self.vdbench_path, filename=self.perf_run_profile,
                                                   timeout=self.perf_run_timeout)
        fun_test.log("Vdbench output result: {}".format(vdbench_result))
        fun_test.test_assert(vdbench_result,
                             "Vdbench run is completed for profile {}".format(self.perf_run_config_file))

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

        row_data_dict = {}
        vdbench_run_name = self.perf_run_config_file

        # Vdbench gives cumulative output, Calculating Read/Write bandwidth and IOPS
        if hasattr(self, "read_pct"):
            read_bw = int(round(float(vdbench_result["throughput"]) * self.read_pct))
            read_iops = int(round(float(vdbench_result["iops"]) * self.read_pct))
            write_bw = int(round(float(vdbench_result["throughput"]) * (1 - self.read_pct)))
            write_iops = int(round(float(vdbench_result["iops"]) * (1 - self.read_pct)))
        else:
            read_bw = int(round(float(vdbench_result["throughput"])))
            read_iops = int(round(float(vdbench_result["iops"])))
            write_bw = -1
            write_iops = -1

        row_data_dict["fio_job_name"] = vdbench_run_name
        row_data_dict["readiops"] = read_iops
        row_data_dict["readbw"] = read_bw
        row_data_dict["writeiops"] = write_iops
        row_data_dict["writebw"] = write_bw

        # Converting response values from milliseconds to microseconds
        row_data_dict["readclatency"] = int(round(float(vdbench_result["read_resp"]) * 1000))
        row_data_dict["writelatency"] = int(round(float(vdbench_result["write_resp"]) * 1000))

        # Building the table raw for this variation
        row_data_list = []
        for i in table_data_cols:
            if i not in row_data_dict:
                row_data_list.append(-1)
            else:
                row_data_list.append(row_data_dict[i])
        table_data_rows.append(row_data_list)
        post_results("Performance Table", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="8k data block random readn/write IOPS Performance Table",
                           table_name=self.summary, table_data=table_data)

    def cleanup(self):
        pass


class RandReadWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1: 8k data block random read/write IOPS performance of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RandReadWrite8kBlocks, self).setup()

    def run(self):
        super(RandReadWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocks, self).cleanup()


class SequentialReadWrite1024kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.11.2: 1024k data block sequential read/write IOPS performance"
                                      "of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for 1024k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(SequentialReadWrite1024kBlocks, self).setup()

    def run(self):
        super(SequentialReadWrite1024kBlocks, self).run()

    def cleanup(self):
        super(SequentialReadWrite1024kBlocks, self).cleanup()


if __name__ == "__main__":

    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    ecscript.run()
