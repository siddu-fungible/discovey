from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


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
    num_volumes = fun_test.shared_variables["num_volumes"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volumes, fio_job_name=fio_job_name,
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


def configure_ec_volume(storage_controller, ec_info, command_timeout):
    result = True
    if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
        result = False
        fun_test.critical("Mandatory attributes needed for the EC volume creation is missing in ec_info dictionary")
        return (result, ec_info)

    if "num_volumes" not in ec_info:
        fun_test.critical("Number of volumes needs to be configured is not provided. So going to configure only one"
                          "EC/LSV volume")
        ec_info["num_volumes"] = 1

    ec_info["uuids"] = {}
    ec_info["volume_capacity"] = {}
    ec_info["attach_uuid"] = {}
    ec_info["attach_size"] = {}

    for num in xrange(ec_info["num_volumes"]):
        ec_info["uuids"][num] = {}
        ec_info["uuids"][num]["blt"] = []
        ec_info["uuids"][num]["ec"] = []
        ec_info["uuids"][num]["jvol"] = []
        ec_info["uuids"][num]["lsv"] = []

        # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
        ec_info["volume_capacity"][num] = {}
        ec_info["volume_capacity"][num]["lsv"] = ec_info["capacity"]
        ec_info["volume_capacity"][num]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
        ec_info["volume_capacity"][num]["nparity"] = ec_info["volume_capacity"][num]["ndata"]
        # ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8KB value")
            ec_info["volume_capacity"][num]["jvol"] = ec_info["lsv_chunk_size"] * ec_info["volume_block"]["lsv"] * \
                                                      ec_info["jvol_size_multiplier"]

            for vtype in ["ndata", "nparity"]:
                tmp = int(round(ec_info["volume_capacity"][num][vtype] * (1 + ec_info["lsv_pct"])))
                # Aligning the capacity the nearest nKB(volume block size) boundary
                ec_info["volume_capacity"][num][vtype] = ((tmp + (ec_info["volume_block"][vtype] - 1)) /
                                                          ec_info["volume_block"][vtype]) * \
                                                         ec_info["volume_block"][vtype]

        # Setting the EC volume capacity to ndata times of ndata volume capacity
        ec_info["volume_capacity"][num]["ec"] = ec_info["volume_capacity"][num]["ndata"] * ec_info["ndata"]

        # Adding one more block to the plex volume size to add room for super block
        for vtype in ["ndata", "nparity"]:
            ec_info["volume_capacity"][num][vtype] = ec_info["volume_capacity"][num][vtype] + \
                                                     ec_info["volume_block"][vtype]

        # Configuring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            ec_info["uuids"][num][vtype] = []
            for i in range(ec_info[vtype]):
                this_uuid = utils.generate_uuid()
                ec_info["uuids"][num][vtype].append(this_uuid)
                ec_info["uuids"][num]["blt"].append(this_uuid)
                command_result = storage_controller.create_volume(
                    type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][num][vtype],
                    block_size=ec_info["volume_block"][vtype], name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                    command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating {} {} {} {} {} bytes volume on DUT instance".
                                     format(num, i, vtype, ec_info["volume_types"][vtype],
                                            ec_info["volume_capacity"][num][vtype]))

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        ec_info["uuids"][num]["ec"].append(this_uuid)
        command_result = storage_controller.create_volume(
            type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"][num]["ec"],
            block_size=ec_info["volume_block"]["ec"], name="ec_" + this_uuid[-4:], uuid=this_uuid,
            ndata=ec_info["ndata"], nparity=ec_info["nparity"], pvol_id=ec_info["uuids"][num]["blt"],
            command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Creating {} {}:{} {} bytes EC volume on DUT instance".
                             format(num, ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"][num]["ec"]))
        ec_info["attach_uuid"][num] = this_uuid
        ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["ec"]

        # Configuring LS volume and its associated journal volume based on the script config setting
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            ec_info["uuids"][num]["jvol"] = utils.generate_uuid()
            command_result = storage_controller.create_volume(
                type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"][num]["jvol"],
                block_size=ec_info["volume_block"]["jvol"], name="jvol_" + this_uuid[-4:],
                uuid=ec_info["uuids"][num]["jvol"], command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes Journal volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["jvol"]))

            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["lsv"].append(this_uuid)
            command_result = storage_controller.create_volume(
                type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"][num]["lsv"],
                block_size=ec_info["volume_block"]["lsv"], name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                group=ec_info["ndata"], jvol_uuid=ec_info["uuids"][num]["jvol"], pvol_id=ec_info["uuids"][num]["ec"],
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes LS volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["lsv"]))
            ec_info["attach_uuid"][num] = this_uuid
            ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["lsv"]

    return (result, ec_info)


def unconfigure_ec_volume(storage_controller, ec_info, command_timeout):
    # Unconfiguring LS volume based on the script config setting
    for num in xrange(ec_info["num_volumes"]):
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            this_uuid = ec_info["uuids"][num]["lsv"][0]
            command_result = storage_controller.delete_volume(
                type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"][num]["lsv"],
                block_size=ec_info["volume_block"]["lsv"], name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {} bytes LS volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["lsv"]))

            this_uuid = ec_info["uuids"][num]["jvol"]
            command_result = storage_controller.delete_volume(
                type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"][num]["jvol"],
                block_size=ec_info["volume_block"]["jvol"], name="jvol_" + this_uuid[-4:], uuid=this_uuid,
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {} bytes Journal volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["jvol"]))

        # Unconfiguring EC volume configured on top of BLT volumes
        this_uuid = ec_info["uuids"][num]["ec"][0]
        command_result = storage_controller.delete_volume(
            type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"][num]["ec"],
            block_size=ec_info["volume_block"]["ec"], name="ec_" + this_uuid[-4:], uuid=this_uuid,
            command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting {} {}:{} {} bytes EC volume on DUT instance".
                             format(num, ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"][num]["ec"]))

        # Unconfiguring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            for i in range(ec_info[vtype]):
                this_uuid = ec_info["uuids"][num][vtype][i]
                command_result = storage_controller.delete_volume(
                    type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][num][vtype],
                    block_size=ec_info["volume_block"][vtype], name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                    command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} {} {} {} bytes volume on DUT instance".
                                     format(num, i, vtype, ec_info["volume_types"][vtype],
                                            ec_info["volume_capacity"][num][vtype]))


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 2
            self.command_timeout = 5
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        self.fs = topology.get_dut_instance(index=self.f1_in_use)
        self.f1 = self.fs.get_f1(index=self.f1_in_use)
        self.db_log_time = get_data_collection_time()
        fun_test.log("Data collection time: {}".format(self.db_log_time))

        self.storage_controller = self.f1.get_dpc_storage_controller()

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if self.testbed_type == "fs-6" and host_ip != "poc-server-01":
                continue
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                self.end_host = host_info["host_obj"]
                self.test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                self.fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(self.fpg_inteface_index))
                break
        else:
            fun_test.test_assert(False, "Host found with Test Interface")

        self.test_network = self.csr_network[str(self.fpg_inteface_index)]
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Fetching NUMA node from Network host for mentioned Ethernet Adapter card
        lspci_output = self.end_host.lspci(grep_filter=self.ethernet_adapter)
        fun_test.simple_assert(lspci_output, "Ethernet Adapter Detected")
        adapter_id = lspci_output[0]['id']
        fun_test.simple_assert(adapter_id, "Ethernet Adapter Bus ID Retrieved")
        lspci_verbose_output = self.end_host.lspci(slot=adapter_id, verbose=True)
        numa_node = lspci_verbose_output[0]['numa_node']
        fun_test.test_assert(numa_node, "Ethernet Adapter NUMA Node Retrieved")

        # Fetching NUMA CPUs for above fetched NUMA Node
        lscpu_output = self.end_host.lscpu(grep_filter="node{}".format(numa_node))
        fun_test.simple_assert(lscpu_output, "CPU associated to Ethernet Adapter NUMA")

        self.numa_cpus = lscpu_output.values()[0]
        fun_test.test_assert(self.numa_cpus, "CPU associated to Ethernet Adapter NUMA")
        fun_test.log("Ethernet Adapter: {}, NUMA Node: {}, NUMA CPU: {}".format(self.ethernet_adapter, numa_node,
                                                                                self.numa_cpus))

        fun_test.shared_variables["numa_cpus"] = self.numa_cpus

        # Configuring Linux host
        host_up_status = self.end_host.reboot(timeout=self.command_timeout, max_wait_time=self.reboot_timeout,
                                              reboot_initiated_wait_time=self.reboot_timeout)
        fun_test.test_assert(host_up_status, "End Host {} is up".format(self.end_host.host_ip))

        interface_ip_config = "ip addr add {} dev {}".format(self.test_network["test_interface_ip"],
                                                             self.test_interface_name)
        interface_mac_config = "ip link set {} address {}".format(self.test_interface_name,
                                                                  self.test_network["test_interface_mac"])
        link_up_cmd = "ip link set {} up".format(self.test_interface_name)
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

        interface_up_status = self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                             action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        route_add_status = self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                                      gateway=self.test_network["test_net_route"]["gw"],
                                                      outbound_interface=self.test_interface_name,
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

    def cleanup(self):

        come_reboot = False
        try:
            self.ec_info = fun_test.shared_variables["ec_info"]
            self.remote_ip = fun_test.shared_variables["remote_ip"]
            self.attach_transport = fun_test.shared_variables["attach_transport"]
            self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
            if fun_test.shared_variables["ec"]["setup_created"]:
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid, ns_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                unconfigure_ec_volume(storage_controller=self.storage_controller, ec_info=self.ec_info,
                                      command_timeout=self.command_timeout)

                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Storage Controller Delete")
        except Exception as ex:
            fun_test.critical(str(ex))
            come_reboot = True

        try:
            if come_reboot:
                self.fs.fpga_initialize()
                fun_test.log("Unexpected exit: Rebooting COMe to ensure next script execution won't ged affected")
                self.fs.come_reset(max_wait_time=self.reboot_timeout)
        except Exception as ex:
            fun_test.critical(str(ex))

        self.storage_controller.disconnect()
        fun_test.sleep("Allowing buffer time before clean-up", 30)
        fun_test.shared_variables["topology"].cleanup()


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
        self.end_host = fun_test.shared_variables["end_host"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.numa_cpus = fun_test.shared_variables["numa_cpus"]

        fun_test.shared_variables["attach_transport"] = self.attach_transport
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            # Enabling counter, performs atomic ops for every WU dispatched and is not recommended for perf runs
            """"# Configuring the controller
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                             command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT")"""

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

            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(ctrlr_id=0,
                                                                       ctrlr_uuid=self.ctrlr_uuid,
                                                                       ctrlr_type="BLOCK",
                                                                       transport=self.attach_transport,
                                                                       remote_ip=self.remote_ip,
                                                                       subsys_nqn=self.nvme_subsystem,
                                                                       host_nqn=self.remote_ip,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create Storage Controller for {} with controller uuid {} on DUT".
                                 format(self.attach_transport, self.ctrlr_uuid))

            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                    ns_id=num + 1, vol_uuid=self.ec_info["attach_uuid"][num], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

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

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

        if not fun_test.shared_variables["ec"]["nvme_connect"]:
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

            lsblk_output = self.end_host.lsblk("-b")
            fun_test.simple_assert(lsblk_output, "Listing available volumes")

            # Checking that the above created BLT volume is visible to the end host
            self.nvme_block_device_list = []
            for num in xrange(self.ec_info["num_volumes"]):
                volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(num+1)
                for volume_name in lsblk_output:
                    match = re.search(volume_pattern, volume_name)
                    if match:
                        self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(num+1)
                        self.nvme_block_device_list.append(self.nvme_block_device)
                        self.volume_name = self.nvme_block_device.replace("/dev/", "")
                        fun_test.test_assert_expected(expected=self.volume_name,
                                                      actual=lsblk_output[volume_name]["name"],
                                                      message="{} device available".format(self.volume_name))
                        break
                else:
                    fun_test.test_assert(False, "{} device available".format(self.volume_name))
                fun_test.log("NVMe Block Device/s: {}".format(self.nvme_block_device_list))

            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["ec"]["nvme_connect"] = True

            self.fio_filename = ":".join(self.nvme_block_device_list)
            fun_test.shared_variables["self.fio_filename"] = self.fio_filename

        # Executing the FIO command to fill the volume to it's capacity
        if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:

            fun_test.log("Executing the FIO command to perform sequential write to volume")
            fio_output = self.end_host.pcie_fio(filename=self.fio_filename, cpus_allowed=self.numa_cpus,
                                                **self.warm_up_fio_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Pre-populating the volume")

            fun_test.shared_variables["ec"]["warmup_io_completed"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
            self.fio_filename = fun_test.shared_variables["self.fio_filename"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
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

        # Going to run the FIO test for the block size and iodepth combo listed in fio_numjobs_iodepth
        fio_result = {}
        fio_output = {}

        for k, v in self.fio_cmd_args.iteritems():
            if k == "bs":
                fio_block_size = self.fio_cmd_args["bs"]
                break
            if k == "bssplit":
                fio_block_size = "Mixed"
                break

        for combo in self.fio_numjobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}

            fio_num_jobs = combo.split(',')[0].strip('() ')
            fio_iodepth = combo.split(',')[1].strip('() ')

            for mode in self.fio_modes:
                """if hasattr(self, self.fio_cmd_args["bs"]):
                    fio_block_size = self.fio_cmd_args["bs"]
                else:
                    fio_block_size = "Mixed"""""
                fio_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_num_jobs)
                size = self.ec_info["capacity"] / (1024 ** 3)
                row_data_dict["size"] = str(size) + "G"

                fun_test.sleep("Waiting in between iterations", self.iter_interval)
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(mode, fio_block_size, fio_iodepth, fio_num_jobs))
                fio_job_name = "{}_iodepth_{}_vol_8".format(self.fio_job_name, str(int(fio_iodepth) * int(fio_num_jobs)))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.fio_filename, rw=mode,
                                                                 numjobs=fio_num_jobs, iodepth=fio_iodepth,
                                                                 name=fio_job_name, cpus_allowed=self.numa_cpus,
                                                                 **self.fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                fun_test.test_assert(fio_output[combo][mode],
                                     "FIO {} test with the Block Size {} IO depth {} and Numjobs {}"
                                     .format(mode, fio_block_size, fio_iodepth, fio_num_jobs))

                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value))
                        row_data_dict[op + field] = fio_output[combo][mode][op][field]

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                # Commenting post_results to avoid dashboard update
                # post_results("Inspur Performance Test", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for combo in self.fio_numjobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class RandReadWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1: 8k data block random read/write IOPS performance of Multiple "
                                      "EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RandReadWrite8kBlocks, self).setup()

    def run(self):
        super(RandReadWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocks, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    ecscript.run()
