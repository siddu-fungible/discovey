from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.fun.fs import Fs
from datetime import datetime
import re
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
import fun_global

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using Vdbench
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
            if ec_info['compress']:
                command_result = storage_controller.create_volume(type=ec_info["volume_types"]["lsv"],
                                                                  capacity=ec_info["volume_capacity"][num]["lsv"],
                                                                  block_size=ec_info["volume_block"]["lsv"],
                                                                  name="lsv_" + this_uuid[-4:],
                                                                  uuid=this_uuid,
                                                                  group=ec_info["ndata"],
                                                                  jvol_uuid=ec_info["uuids"][num]["jvol"],
                                                                  pvol_id=ec_info["uuids"][num]["ec"],
                                                                  zip_effort=ec_info['zip_effort'],
                                                                  zip_filter=ec_info["zip_filter"],
                                                                  compress=ec_info['compress'],
                                                                  command_duration=command_timeout)
            else:
                command_result = storage_controller.create_volume(
                    type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"][num]["lsv"],
                    block_size=ec_info["volume_block"]["lsv"], name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                    group=ec_info["ndata"], jvol_uuid=ec_info["uuids"][num]["jvol"],
                    pvol_id=ec_info["uuids"][num]["ec"],
                    command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes LS volume on DUT instance".
                                 format(num, ec_info["volume_capacity"][num]["lsv"]))
            ec_info["attach_uuid"][num] = this_uuid
            ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["lsv"]

    return (result, ec_info)


def unconfigure_ec_volume(storage_controller, ec_info, command_timeout):
    # Unconfiguring LS volume based on the script config settting
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
            self.retries = 24
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=self.f1_in_use, custom_boot_args=self.bootargs)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        self.fs = topology.get_dut_instance(index=self.f1_in_use)
        self.db_log_time = datetime.now()

        self.come = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip,
                                                    target_port=self.come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                self.end_host = host_info["host_obj"]
                self.test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                self.fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(self.fpg_inteface_index))
                break
        else:
            fun_test.test_assert(False, "Host found with Test Interface")

        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Configuring Linux host
        host_up_status = self.end_host.reboot(timeout=self.command_timeout, retries=self.retries)
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
        try:
            self.ec_info = fun_test.shared_variables["ec_info"]
            self.remote_ip = fun_test.shared_variables["remote_ip"]
            self.attach_transport = fun_test.shared_variables["attach_transport"]
            if fun_test.shared_variables["ec"]["setup_created"]:
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.volume_detach_remote(
                        ns_id=num + 1, uuid=self.ec_info["attach_uuid"][num], huid=self.huid, ctlid=self.ctlid,
                        remote_ip=self.remote_ip, transport=self.attach_transport,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                unconfigure_ec_volume(storage_controller=self.storage_controller, ec_info=self.ec_info,
                                      command_timeout=self.command_timeout)

            self.storage_controller.disconnect()
            fun_test.sleep("Allowing buffer time before clean-up", 30)
            fun_test.shared_variables["topology"].cleanup()
        except Exception as ex:
            fun_test.critical(ex.message)


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
                    ns_id=num + 1, uuid=self.ec_info["attach_uuid"][num], huid=self.huid, ctlid=self.ctlid,
                    remote_ip=self.remote_ip, transport=self.attach_transport, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

            fun_test.shared_variables["ec"]["setup_created"] = True

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

            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["ec"]["nvme_connect"] = True

        # Executing the vdbench command to fill the volume to it's capacity
        if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
            fun_test.log("Building the volume pre-populte config file for Vdbench")
            self.volume_fill_file = "{}/{}".format(self.vdbench_path, self.warm_up_config_file)
            self.end_host.create_file(file_name=self.volume_fill_file, contents=self.warm_up_vdb_config)

            fun_test.log("Starting Vdbench to pre-populate all the volumes")
            vdbench_result = self.end_host.vdbench(path=self.vdbench_path, filename=self.volume_fill_file,
                                                   timeout=self.warm_up_timeout)
            fun_test.log("Vdbench output result: {}".format(vdbench_result))
            fun_test.test_assert(vdbench_result,
                                 "Vdbench run is completed for profile {}".format(self.warm_up_config_file))

            fun_test.shared_variables["ec"]["warmup_io_completed"] = True

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

        # Prepare vdbench run config file
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
        row_data_dict["mode"] = self.operation

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
        8. Run the Performance for 1024k transfer size Sequential read/write IOPS
        """)

    def setup(self):
        super(SequentialReadWrite1024kBlocks, self).setup()

    def run(self):
        super(SequentialReadWrite1024kBlocks, self).run()

    def cleanup(self):
        super(SequentialReadWrite1024kBlocks, self).cleanup()


class IntegratedModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Inspur TC 8.11.3: Integrated  model read/write IOPS performance of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for Integrated Model read/write IOPS
        """)

    def setup(self):
        super(IntegratedModelReadWriteIOPS, self).setup()

    def run(self):
        super(IntegratedModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(IntegratedModelReadWriteIOPS, self).cleanup()


class OLTPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Inspur TC 8.11.4: OLTP Model read/read IOPS performance of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for OLTP model read/write IOPS
        """)

    def setup(self):
        super(OLTPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLTPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLTPModelReadWriteIOPS, self).cleanup()


class OLAPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Inspur TC 8.11.5: OLAP Model read/write IOPS performance of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for OLAP model Random read/write IOPS
        """)

    def setup(self):
        super(OLAPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLAPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLAPModelReadWriteIOPS, self).cleanup()


class RandReadWrite8kBlocksLatencyTest(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Inspur TC 8.11.6: 8k data block random read/write latency test of EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using vdbench
        8. Run the Performance for 8k transfer size Random read/write latency
        """)

    def setup(self):
        super(RandReadWrite8kBlocksLatencyTest, self).setup()

    def run(self):
        super(RandReadWrite8kBlocksLatencyTest, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocksLatencyTest, self).cleanup()


class RandReadWrite8kBlocksCompEffortAuto(ECVolumeLevelTestcase):
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
        super(RandReadWrite8kBlocksCompEffortAuto, self).setup()

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")
        self.end_host = fun_test.shared_variables["end_host"]
        fun_test.sleep("Interval before starting traffic", self.iter_interval)
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

        for test in self.test_parameters:
            if test['compress_percent'] != 0:
                warmup_profile = "{}/{}".format(self.vdbench_path, self.warm_up_config_file)
                self.end_host.create_file(file_name=warmup_profile, contents=test['warmup_command'])
                fun_test.test_assert(self.end_host.vdbench(path=self.vdbench_path,
                                                           filename=warmup_profile,
                                                           timeout=self.perf_run_timeout),
                                     "Execute warmup write with Compression ratio {}".format(test['compress_percent']))

            run_profile = "{}/{}".format(self.vdbench_path, test['perf_run_config_profile'])
            self.end_host.create_file(file_name=run_profile, contents=test['perf_run_vdb_config'])
            vdbench_result = self.end_host.vdbench(path=self.vdbench_path,
                                                   filename=run_profile,
                                                   timeout=self.perf_run_timeout)
            fun_test.test_assert(vdbench_result,
                                 "Run Vdbench randread+write with 70% read, compression percent: {}".format(
                                     test['compress_percent']))
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

            row_data_dict["fio_job_name"] = test['perf_run_config_file']
            row_data_dict["readiops"] = read_iops
            row_data_dict["readbw"] = read_bw
            row_data_dict["writeiops"] = write_iops
            row_data_dict["writebw"] = write_bw
            row_data_dict["mode"] = self.operation

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
            if fun_global.is_production_mode():
                post_results("Performance Table", test_method, *row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="8k data block random readn/write IOPS Performance Table",
                               table_name=test['name'], table_data=table_data)

    def cleanup(self):
        super(RandReadWrite8kBlocksCompEffortAuto, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    # ecscript.add_test_case(RandReadWrite8kBlocks())
    # ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    # ecscript.add_test_case(IntegratedModelReadWriteIOPS())
    # ecscript.add_test_case(OLTPModelReadWriteIOPS())
    # ecscript.add_test_case(OLAPModelReadWriteIOPS())
    ecscript.add_test_case(RandReadWrite8kBlocksCompEffortAuto())
    # ecscript.add_test_case(RandReadWrite8kBlocksLatencyTest())
    ecscript.run()
