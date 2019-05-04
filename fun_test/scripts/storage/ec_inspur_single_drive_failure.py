from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.host.linux import Linux
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
        fun_test.log("{} Testbed Config: {}".format(self.testbed_type, self.testbed_config))
        fun_test.simple_assert(self.fs_spec, "FS Spec for {}".format(self.testbed_type))
        fun_test.simple_assert(self.testbed_config, "Testbed Config for {}".format(self.testbed_type))

        # Getting the first network host
        for interface in self.testbed_config["dut_info"][str(self.f1_in_use)]["fpg_interface_info"]:
            if "host_info" in self.testbed_config["dut_info"][str(self.f1_in_use)]["fpg_interface_info"][interface]:
                self.nw_hostname = \
                    self.testbed_config["dut_info"][str(self.f1_in_use)]["fpg_interface_info"][interface]["host_info"]["name"]
                break

        self.host_config = fun_test.get_asset_manager().get_host_spec(self.nw_hostname)
        fun_test.log("{} Host Config: {}".format(self.nw_hostname, self.host_config))
        fun_test.simple_assert(self.host_config, "Host Config for {}".format(self.nw_hostname))

        fun_test.shared_variables["testbed_type"] = self.testbed_type
        fun_test.shared_variables["fs_spec"] = self.fs_spec
        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["host_config"] = self.host_config
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["attach"] = self.attach
        fun_test.shared_variables["test_network"] = self.test_network

        # Initializing the FS
        self.fs = Fs.get(boot_args=self.bootargs, disable_f1_index=self.disable_f1_index)
        fun_test.test_assert(self.fs.bootup(reboot_bmc=False, power_cycle_come=True), "FS bootup")

        self.f1 = self.fs.get_f1(index=self.f1_in_use)
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1"] = self.f1

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
        self.storage_controller.disconnect()
        fun_test.sleep("Allowing buffer time before calling fs clean-up", 60)
        self.fs.cleanup()


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

        self.testbed_type = fun_test.shared_variables["testbed_type"]
        self.fs_spec = fun_test.shared_variables["fs_spec"]
        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.host_config = fun_test.shared_variables["host_config"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.attach = fun_test.shared_variables["attach"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.end_host = fun_test.shared_variables["end_host"]

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.volume_configured = False
        self.volume_attached = False

        # Proceeding to configure the EC volume
        # Configuring the controller
        command_result = {}
        command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                         command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

        command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

        (ec_config_status, self.ec_info) = self.configure_ec_volume(self.ec_info, self.command_timeout)
        fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

        self.volume_configured = True
        fun_test.log("EC details after configuring EC Volume:")
        for k, v in self.ec_info.items():
            fun_test.log("{}: {}".format(k, v))

        # Attaching/Exporting all the EC/LS volumes to the external server
        self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip

        for num in xrange(self.ec_info["num_volumes"]):
            command_result = self.storage_controller.volume_attach_remote(
                ns_id=num+1, uuid=self.ec_info["attach_uuid"][num], huid=self.attach["huid"],
                ctlid=self.attach["ctlid"], remote_ip=self.remote_ip, transport=self.attach["transport"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

        self.volume_attached = True
        fun_test.shared_variables["ec_info"] = self.ec_info


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

        # Performing nvme connect with the expected number of I/O queues
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(
                self.attach["transport"].lower(), self.test_network["f1_loopback_ip"], str(self.attach["port"]),
                self.nvme_subsystem)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                self.attach["transport"].lower(), self.test_network["f1_loopback_ip"], str(self.attach["port"]),
                self.nvme_subsystem, str(self.io_queues))

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("NVME Connect Status Output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        lsblk_output = self.end_host.lsblk("-b")
        fun_test.simple_assert(lsblk_output, "Listing available volumes")

        # Checking that the above created EC volume is visible to the end host after NVME connect
        volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
        self.nvme_block_device_list = []
        self.volume_name_list = []
        for volume_name in lsblk_output:
            match = re.search(volume_pattern, volume_name)
            if match:
                ctlr_id = match.group(1)
                ns_id = match.group(2)
                self.nvme_block_device_list.append(self.nvme_device + str(ctlr_id) + "n" + str(ns_id))
                self.volume_name_list.append(self.nvme_block_device.replace("/dev/", ""))
                fun_test.test_assert_expected(expected=self.volume_name_list[-1],
                                              actual=lsblk_output[volume_name]["name"],
                                              message="{} device available".format(self.volume_name_list[-1]))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                              message="{} device type check".format(self.volume_name_list[-1]))
                fun_test.test_assert_expected(expected=self.ec_info["attach_size"][ns_id + 1],
                                              actual=lsblk_output[volume_name]["size"],
                                              message="{} volume size check".format(self.volume_name_list[-1]))

        # Total number of volumes available should be equal to the ec_info["num_volumes"]
        self.nvme_block_device_list.sort()
        self.volume_name_list.sort()
        fun_test.test_assert_expected(expected=self.ec_info["num_volumes"], actual=len(self.volume_name_list),
                                      message="Number of volumes available")

        fun_test.shared_variables["nvme_block_device_list"] = self.nvme_block_device_list
        fun_test.shared_variables["volume_name_list"] = self.volume_name_list

        # Disable the udev daemon which will skew the read stats of the volume during the test
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.end_host.systemctl(service_name=service, action="stop")
            fun_test.test_assert(service_status, "Stopping {} service".format(service))

    def run(self):

        # Checking whether the ec_info is having the drive and device ID for the EC's plex volumes
        # Else going to extract the same
        if "device_id" not in self.ec_info:
            fun_test.log("Drive and Device ID of the EC volume's plext volumes are not available in the ec_info..."
                         "So going to pull that info")
            self.ec_info["drive_uuid"] = {}
            self.ec_info["device_id"] = {}
            for num in xrange(self.ec_info["num_volumes"]):
                self.ec_info["drive_uuid"][num] = []
                self.ec_info["device_uuid"][num] = []
                for blt_uuid in self.ec_info["uuids"][num]["blt"]:
                    blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid,
                                                             "stats")
                    blt_stats = self.storage_controller.peek(blt_props_tree)
                    fun_test.simple_assert(blt_stats["status"], "Stats of BLT Volume {}".format(blt_uuid))
                    if "drive_uuid" in blt_stats["data"]:
                        self.ec_info["drive_uuid"][num].append(blt_stats["data"]["drive_uuid"])
                    else:
                        fun_test.simple_assert(blt_stats["data"].get("drive_uuid"), "Drive UUID of BLT volume {}".
                                             format(blt_uuid))
                    drive_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "drives",
                                                            blt_stats["data"]["drive_uuid"])
                    drive_stats = self.storage_controller.peek(drive_props_tree)
                    fun_test.simple_assert(drive_stats["status"], "Stats of the drive {}".
                                           format(blt_stats["data"]["drive_uuid"]))
                    if "drive_id" in drive_stats["data"]:
                        self.ec_info["device_id"][num].append(drive_stats["data"]["drive_id"])
                    else:
                        fun_test.simple_assert(drive_stats["data"].get("drive_id"), "Device ID of the drive {}".
                                             format(blt_stats["data"]["drive_uuid"]))


        # Creating the filesystem in the volumes configured and available to the host
        if self.fs_type == "xfs":
            install_status = self.end_host.install_package("xfsprogs")
            fun_test.test_assert(install_status, "Installing XFS Package")

        for num in xrange(self.ec_info["num_volumes"]):
            size = self.ec_info["attach_size"][num]
            # Set the timeout for the filesystem create command based on its size
            fs_create_timeout = (size / self.f1_fs_timeout_ratio[0]) * self.f1_fs_timeout_ratio[1]
            if fs_create_timeout < self.min_timeout:
                fs_create_timeout = self.min_timeout
            fs_status = self.end_host.create_filesystem(self.fs_type, self.nvme_block_device_list[num],
                                                        timeout=fs_create_timeout)
            fun_test.test_assert(fs_status, "Creating {} filesystem on EC volume {}".format(self.fs_type,
                                                                                            self.volume_name_list[num]))
            command_result = self.end_host.create_directory(self.mount_point + str(num))
            fun_test.test_assert(command_result, "Creating mount point directory {}".
                                 format(self.mount_point + str(num)))
            command_result = self.end_host.mount_volume(self.nvme_block_device_list[num], self.mount_point + str(num))
            fun_test.simple_assert(command_result, "Mounting EC volume {} on {}".
                                   format(self.nvme_block_device_list[num], self.mount_point + str(num)))
            lsblk_output = self.end_host.lsblk("-b")
            fun_test.test_assert_expected(expected=self.mount_point + str(num),
                                          actual=lsblk_output[self.volume_name_list[num]]["mount_point"],
                                          message="Mounting EC volume {} on {}".format(self.nvme_block_device_list[num],
                                                                                       self.mount_point + str(num)))

        # Creating input file
        self.dd_create_file["count"] = self.test_file_size / self.dd_write_args["block_size"]

        # Write a file into the EC volume of size self.input_file_size bytes
        return_size = self.host.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
        fun_test.test_assert_expected(self.input_file_size, return_size, "Creating {} bytes test input file".
                                      format(self.test_file_size))
        self.input_md5sum = self.host.md5sum(file_name=self.dd_create_file["output_file"],
                                             timeout=self.dd_create_file["count"])
        fun_test.test_assert(self.input_md5sum, "Finding md5sum of input file {}".
                             format(self.dd_create_file["output_file"]))



    def cleanup(self):

        if self.volume_attached:
            # Detaching all the EC/LS volumes to the external server
            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.volume_detach_remote(
                    ns_id=num + 1, uuid=self.ec_info["attach_uuid"][num], huid=self.attach['huid'],
                    ctlid=self.attach['ctlid'], remote_ip=self.remote_ip, transport=self.attach['transport'],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

        if self.volume_configured:
            # Unconfiguring all the LSV/EC and it's plex volumes
            self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info, command_timeout=self.command_timeout)


class SingleClientSingleVolumeWithoutBP(ECVolumeLevelTestcase):
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
        super(SingleClientSingleVolumeWithoutBP, self).setup()

    def run(self):
        super(SingleClientSingleVolumeWithoutBP, self).run()

    def cleanup(self):
        super(SingleClientSingleVolumeWithoutBP, self).cleanup()

if __name__ == "__main__":

    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(SingleClientSingleVolumeWithoutBP())
    ecscript.run()
