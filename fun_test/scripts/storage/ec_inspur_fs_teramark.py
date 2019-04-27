from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.host.linux import Linux
from lib.host.palladium import DpcshProxy
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.fs import Fs
from datetime import datetime

'''
Script to track the performance of various read write combination of Erasure Coded volume using FIO
'''

tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_EMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "pci_mode": "all",
            "bootarg": "app=mdt_test,load_mods,hw_hsu_test --serial --memvol --dis-stats --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze",
            "disable_f1_index": 1,
            "f1_in_use": 0,
            "huid": 7,
            "ctlid": 0
        },
    },
    "dpcsh_proxy": {
        "ip": "server120",
        "user": REGRESSION_USER,
        "passwd": REGRESSION_USER_PASSWORD,
        "dpcsh_port": 50221,
        "dpcsh_tty": "/dev/ttyUSB8"
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST,
            "ip": "cadence-pc-5",
            "user": "localadmin",
            "passwd": "Precious1*",
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


def configure_ec_volume(storage_controller, ec_info, command_timeout):

    result = True
    if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
        result = False
        fun_test.critical("Mandatory attributes needed for the EC volume creation is missing in ec_info dictionary")
        return (result, ec_info)

    ec_info["uuids"] = {}
    ec_info["uuids"]["blt"] = []
    ec_info["uuids"]["ec"] = []
    ec_info["uuids"]["jvol"] = []
    ec_info["uuids"]["lsv"] = []

    # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
    ec_info["volume_capacity"] = {}
    ec_info["volume_capacity"]["lsv"] = ec_info["capacity"]
    ec_info["volume_capacity"]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
    ec_info["volume_capacity"]["nparity"] = ec_info["volume_capacity"]["ndata"]
    # ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

    if "use_lsv" in ec_info and ec_info["use_lsv"]:
        fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                     "rounding that to the nearest 8KB value")
        ec_info["volume_capacity"]["jvol"] = ec_info["lsv_chunk_size"] * ec_info["volume_block"]["lsv"] * \
                                             ec_info["jvol_size_multiplier"]

        for vtype in ["ndata", "nparity"]:
            tmp = int(round(ec_info["volume_capacity"][vtype] * (1 + ec_info["lsv_pct"])))
            # Aligning the capacity the nearest nKB(volume block size) boundary
            ec_info["volume_capacity"][vtype] = ((tmp + (ec_info["volume_block"][vtype] - 1)) /
                                                 ec_info["volume_block"][vtype]) * \
                                                ec_info["volume_block"][vtype]

    # Setting the EC volume capacity to ndata times of ndata volume capacity
    ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

    # Adding one more block to the plex volume size to add room for super block
    for vtype in ["ndata", "nparity"]:
        ec_info["volume_capacity"][vtype] = ec_info["volume_capacity"][vtype] + ec_info["volume_block"][vtype]

    # Configuring ndata and nparity number of BLT volumes
    for vtype in ["ndata", "nparity"]:
        ec_info["uuids"][vtype] = []
        for i in range(ec_info[vtype]):
            this_uuid = utils.generate_uuid()
            ec_info["uuids"][vtype].append(this_uuid)
            ec_info["uuids"]["blt"].append(this_uuid)
            command_result = storage_controller.create_volume(
                type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][vtype],
                block_size=ec_info["volume_block"][vtype], name=vtype+"_"+this_uuid[-4:], uuid=this_uuid,
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} {} {} {} bytes volume on DUT instance".
                                 format(i, vtype, ec_info["volume_types"][vtype], ec_info["volume_capacity"][vtype]))

    # Configuring EC volume on top of BLT volumes
    this_uuid = utils.generate_uuid()
    ec_info["uuids"]["ec"].append(this_uuid)
    command_result = storage_controller.create_volume(
        type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"]["ec"],
        block_size=ec_info["volume_block"]["ec"], name="ec_"+this_uuid[-4:], uuid=this_uuid,
        ndata=ec_info["ndata"], nparity=ec_info["nparity"], pvol_id=ec_info["uuids"]["blt"],
        command_duration=command_timeout)
    fun_test.test_assert(command_result["status"], "Creating {}:{} {} bytes EC volume on DUT instance".
                         format(ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"]["ec"]))
    ec_info["attach_uuid"] = this_uuid
    ec_info["attach_size"] = ec_info["volume_capacity"]["ec"]

    # Configuring LS volume and its associated journal volume based on the script config setting
    if "use_lsv" in ec_info and ec_info["use_lsv"]:
        ec_info["uuids"]["jvol"] = utils.generate_uuid()
        command_result = storage_controller.create_volume(
            type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"]["jvol"],
            block_size=ec_info["volume_block"]["jvol"], name="jvol_"+this_uuid[-4:], uuid=ec_info["uuids"]["jvol"],
            command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Creating {} bytes Journal volume on DUT instance".
                             format(ec_info["volume_capacity"]["jvol"]))

        this_uuid = utils.generate_uuid()
        ec_info["uuids"]["lsv"].append(this_uuid)
        command_result = storage_controller.create_volume(
            type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"]["lsv"],
            block_size=ec_info["volume_block"]["lsv"], name="lsv_"+this_uuid[-4:], uuid=this_uuid,
            group=ec_info["ndata"], jvol_uuid=ec_info["uuids"]["jvol"], pvol_id=ec_info["uuids"]["ec"],
            command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Creating {} bytes LS volume on DUT instance".
                             format(ec_info["volume_capacity"]["lsv"]))
        ec_info["attach_uuid"] = this_uuid
        ec_info["attach_size"] = ec_info["volume_capacity"]["lsv"]

    return (result, ec_info)


def unconfigure_ec_volume(storage_controller, ec_info, command_timeout):

    # Unconfiguring LS volume based on the script config settting
    if "use_lsv" in ec_info and ec_info["use_lsv"]:
        this_uuid = ec_info["uuids"]["lsv"][0]
        command_result = storage_controller.delete_volume(
            type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"]["lsv"],
            block_size=ec_info["volume_block"]["lsv"], name="lsv_"+this_uuid[-4:], uuid=this_uuid,
            command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting {} bytes LS volume on DUT instance".
                             format(ec_info["volume_capacity"]["lsv"]))

        this_uuid = ec_info["uuids"]["jvol"]
        command_result = storage_controller.delete_volume(
            type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"]["jvol"],
            block_size=ec_info["volume_block"]["jvol"], name="jvol_"+this_uuid[-4:], uuid=this_uuid,
            command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting {} bytes Journal volume on DUT instance".
                             format(ec_info["volume_capacity"]["jvol"]))

    # Unconfiguring EC volume configured on top of BLT volumes
    this_uuid = ec_info["uuids"]["ec"][0]
    command_result = storage_controller.delete_volume(
        type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"]["ec"],
        block_size=ec_info["volume_block"]["ec"], name="ec_"+this_uuid[-4:], uuid=this_uuid,
        command_duration=command_timeout)
    fun_test.log(command_result)
    fun_test.test_assert(command_result["status"], "Deleting {}:{} {} bytes EC volume on DUT instance".
                         format(ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"]["ec"]))

    # Unconfiguring ndata and nparity number of BLT volumes
    for vtype in ["ndata", "nparity"]:
        for i in range(ec_info[vtype]):
            this_uuid = ec_info["uuids"][vtype][i]
            command_result = storage_controller.delete_volume(
                type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][vtype],
                block_size=ec_info["volume_block"][vtype], name=vtype+"_"+this_uuid[-4:], uuid=this_uuid,
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {} {} {} bytes volume on DUT instance".
                                 format(i, vtype, ec_info["volume_types"][vtype], ec_info["volume_capacity"][vtype]))


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.deploy()

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

        # Pulling the testbed type and its config
        self.test_bed_type = fun_test.get_job_environment_variable("test_bed_type")
        fun_test.log("Testbed-type: {}".format(self.test_bed_type))
        self.test_bed_spec = fun_test.get_asset_manager().get_fs_by_name(self.test_bed_type)
        fun_test.log("{} Testbed Config: {}".format(self.test_bed_type, self.test_bed_spec))
        fun_test.simple_assert(self.test_bed_spec, "Test-bed spec for {}".format(self.test_bed_type))
        fun_test.shared_variables["test_bed_type"] = self.test_bed_type
        fun_test.shared_variables["test_bed_spec"] = self.test_bed_spec
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use

        # Initializing the FS
        fs = Fs.get(boot_args=self.bootargs, disable_f1_index=self.disable_f1_index)
        fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=True), "FS bootup")

        f1 = fs.get_f1(index=self.f1_in_use)
        fun_test.shared_variables["fs"] = fs
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = datetime.now()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        # Initializing the Network attached host
        end_host_ip = self.test_bed_spec["nw_host"][self.f1_in_use][0]["mgmt_ip"]
        end_host_user = self.test_bed_spec["nw_host"][self.f1_in_use][0]["mgmt_ssh_username"]
        # end_host_passwd = ssh_password=self.test_bed_spec["nw_host"][self.f1_in_use][0]["mgmt_ssh_password"]
        end_host_passwd = self.test_bed_spec["nw_host"][self.f1_in_use][0]["mgmt_ssh_password"]
        self.end_host = Linux(host_ip=end_host_ip, ssh_username=end_host_user, ssh_password=end_host_passwd)
        fun_test.shared_variables["end_host"] = self.end_host

        host_up_status = self.end_host.reboot(timeout=self.command_timeout, retries=self.retries)
        # host_up_status = self.end_host.is_host_up(timeout=self.command_timeout)
        fun_test.test_assert(host_up_status, "End Host {} is up".format(end_host_ip))

        interface_ip_config = "sudo ip addr add {} dev {}".format(
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_ip"],
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_name"])
        interface_mac_config= "sudo ip link set {} address {}".format(
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_name"],
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_mac"])
        link_up_cmd = "sudo ip link set {} up".format(
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_name"])
        static_arp_cmd = "sudo arp -s {} {}".format(
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_net_route"]["gw"],
            self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_net_route"]["arp"])

        interface_ip_config_status = self.end_host.sudo_command(command=interface_ip_config,
                                                                timeout=self.command_timeout)
        fun_test.log("interface_ip_config_status output is: {}".format(interface_ip_config_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Configuring test interface IP address")


        interface_mac_status = self.end_host.sudo_command(command=interface_mac_config,
                                                          timeout=self.command_timeout)
        fun_test.log("interface_mac_status output is: {}".format(interface_mac_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Assigning MAC to test interface")

        link_up_status = self.end_host.sudo_command(command=link_up_cmd, timeout=self.command_timeout)
        fun_test.log("link_up_status output is: {}".format(link_up_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Bringing up test link")

        interface_up_status = self.end_host.ifconfig_up_down(
            interface=self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_name"],
            action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        route_add_status = self.end_host.ip_route_add(
            network=self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_net_route"]["net"],
            gateway=self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_net_route"]["gw"],
            outbound_interface=self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_name"],
            timeout=self.command_timeout)
        fun_test.log("route_add_status output is: {}".format(route_add_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Adding route to F1")

        arp_add_status = self.end_host.sudo_command(command=static_arp_cmd, timeout=self.command_timeout)
        fun_test.log("arp_add_status command output is: {}".format(arp_add_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Adding static ARP to F1 route")

        '''
        # self.end_host.modprobe(module="nvme")
        self.end_host.sudo_command("modprobe nvme")
        fun_test.sleep("nvme module is loaded")
        # self.end_host.modprobe(module="nvme_tcp")
        self.end_host.sudo_command("modprobe nvme_tcp")
        fun_test.sleep("nvme_tcp module is loaded")
        '''

        # Loading the nvme and nvme_tcp modules
        self.end_host.modprobe(module="nvme")
        fun_test.sleep("Loading nvme module", 2)
        command_result = self.end_host.lsmod(module="nvme")
        fun_test.simple_assert(command_result, "Loading nvme module")
        fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

        self.end_host.modprobe(module="nvme_tcp")
        fun_test.sleep("Loading nvme module", 2)
        command_result = self.end_host.lsmod(module="nvme_tcp")
        fun_test.simple_assert(command_result, "Loading nvme module")
        fun_test.test_assert_expected(expected="nvme_tcp", actual=command_result['name'],
                                      message="Loading nvme_tcp module")

        self.storage_controller = f1.get_dpc_storage_controller()
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

        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # self.ec_coding = fun_test.shared_variables["ec_coding"]  # TODO Remove
        # self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])  # TODO Remove
        # if fun_test.shared_variables[self.ec_ratio]["setup_created"]:

        # Detaching and Unconfiguring all the volumes
        '''command_result = self.storage_controller.volume_detach_pcie(
            ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], command_duration=self.command_timeout)'''

        '''self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
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
                command_duration=self.command_timeout)
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
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detaching EC volume on DUT instance")

        # Deleting the EC volume
        command_result = self.storage_controller.delete_volume(
            type=self.volume_types["ec"], capacity=self.volume_capacity["ec"], block_size=self.volume_block["ec"],
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
                    block_size=self.volume_block[vtype], name=vtype+str(i),
                    uuid=self.uuids[self.volume_types[vtype]][i], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} BLT volume on DUT".format(i, vtype))'''

        fun_test.shared_variables["storage_controller"] = self.storage_controller
        self.storage_controller.disconnect()
        fs = fun_test.shared_variables["fs"]
        fs.cleanup()
        '''self.dpcsh_host = DpcshProxy(ip=tb_config["dpcsh_proxy"]["ip"],
                                     dpcsh_port=tb_config["dpcsh_proxy"]["dpcsh_port"],
                                     user=tb_config["dpcsh_proxy"]["user"],
                                     password=tb_config["dpcsh_proxy"]["passwd"])
        status = self.dpcsh_host.stop_dpcsh_proxy(dpcsh_proxy_port=tb_config["dpcsh_proxy"]["dpcsh_port"],
                                                  dpcsh_proxy_tty=tb_config["dpcsh_proxy"]["dpcsh_tty"])
        fun_test.test_assert(status, "Stopped dpcsh with {} in tcp proxy mode".
                             format(tb_config["dpcsh_proxy"]["dpcsh_tty"]))'''


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
        if not hasattr(self, "num_volume"):
            self.num_volume = 1
        # End of benchmarking json file parsing

        self.fs = fun_test.shared_variables["fs"]
        self.f1 = fun_test.shared_variables["f1"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.end_host = fun_test.shared_variables["end_host"]

        self.test_bed_type = fun_test.shared_variables["test_bed_type"]
        self.test_bed_spec = fun_test.shared_variables["test_bed_spec"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]

        # Remove fun_test.shared_variables["ec_coding"] = self.ec_coding  # TODO Remove
        # self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])  # TODO Remove
        self.nvme_block_device = self.nvme_device + "n" + str(self.ns_id)

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False

            # Configuring the controller
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                             command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

            command_result = self.storage_controller.ip_cfg(ip=self.test_bed_spec["f1_loopback_ip"][self.f1_in_use])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

            (ec_config_status, self.ec_info) = configure_ec_volume(self.storage_controller,
                                                                   self.ec_info, self.command_time)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            # Attaching/Exporting the EC/LS volume to the external server
            self.remote_ip = self.test_bed_spec["nw_host"][self.f1_in_use][0]["test_interface_ip"].split('/')[0]
            command_result = self.storage_controller.volume_attach_remote(
                ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], huid=tb_config['dut_info'][0]['huid'],
                ctlid=tb_config['dut_info'][0]['ctlid'], remote_ip=self.remote_ip,
                transport=self.attach_transport, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume on DUT")

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

            fun_test.shared_variables["ns_id"] = self.ns_id
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["remote_ip"] = self.remote_ip
            fun_test.shared_variables["ec"]["setup_created"] = True

            # sudo nvme connect -t tcp -a 29.1.1.1 -s 1099 -n nqn.2017-05.com.fungible:nss-uuid1
            if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                nvme_connect_cmd = "sudo nvme connect -t {} -a {} -s {} -n {}".format(
                    self.attach_transport.lower(), self.test_bed_spec["f1_loopback_ip"][self.f1_in_use],
                    str(self.transport_port), self.nvme_subsystem)
            else:
                nvme_connect_cmd = "sudo nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                    self.attach_transport.lower(), self.test_bed_spec["f1_loopback_ip"][self.f1_in_use],
                    str(self.transport_port), self.nvme_subsystem, str(self.io_queues))

            nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
            fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message="NVME Connect Status")

            # Checking that the above created volume is visible to the end host
            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.ns_id)
            lsblk_output = self.end_host.lsblk()
            fun_test.log("lsblk output is: {}".format(lsblk_output))
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))

            ''''# Disable the udev daemon which will skew the read stats of the volume during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for service in udev_services:
                service_status = self.end_host.systemctl(service_name=service, action="stop")
                fun_test.test_assert(service_status, "Stopping {} service".format(service))'''

            # Executing the FIO command to warm up the system
            if self.warm_up_traffic:
                fun_test.log("Building the volume pre-populte config file")
                self.volume_fill_file = "{}/{}".format(self.vdbench_path, self.warm_up_config_file)
                self.end_host.create_file(file_name=self.volume_fill_file, contents=self.warm_up_vdb_config)

                fun_test.log("Starting Vdbench to pre-populate all the volumes")
                vdbench_result = self.end_host.run_vdbench(path=self.vdbench_path, timeout=self.warm_up_timeout)
                fun_test.log("Vdbench output result: {}".format(vdbench_result))


    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        fun_test.log("Starting Random Read/Write of 8k data block")
        self.end_host = fun_test.shared_variables["end_host"]

        if self.end_host.check_file_directory_exists(path="/usr/local/share/vdbench/single_node_8_11_1"):
            vdbench_result = self.end_host.sudo_command(
                "/usr/local/share/vdbench/vdbench -f /usr/local/share/vdbench/single_node_8_11_1",
                timeout=self.command_timeout * 20)
            fun_test.log("Vdbench output result: {}".format(vdbench_result))

        ''''# self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
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
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the BLT volume having the UUID "
                                                               "{}".format(self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree)
                fun_test.log(command_result)
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

                # Pulling initial volume stats of all the volumes from the DUT in dictionary format
                fun_test.log("Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                             "the test")
                initial_volume_status[combo][mode] = {}
                for vtype in volumes:
                    initial_volume_status[combo][mode][vtype] = {}
                    for index, uuid in enumerate(self.uuids[vtype]):
                        initial_volume_status[combo][mode][vtype][index] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, uuid, "stats")
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree,
                                                                      command_duration=self.command_timeout)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(vtype, index))
                        initial_volume_status[combo][mode][vtype][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(vtype, index))
                        fun_test.log(initial_volume_status[combo][mode][vtype][index])

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
                    fun_test.log(initial_stats[combo][mode][key])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_block_size, fio_iodepth, self.ec_ratio))
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
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
                fun_test.log("Pulling volume stats of all volumes after the FIO test")
                final_volume_status[combo][mode] = {}
                for vtype in volumes:
                    final_volume_status[combo][mode][vtype] = {}
                    for index, uuid in enumerate(self.uuids[vtype]):
                        final_volume_status[combo][mode][vtype][index] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, uuid, "stats")
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree,
                                                                      command_duration=self.command_timeout)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(vtype, index))
                        final_volume_status[combo][mode][vtype][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(vtype, index))
                        fun_test.log(final_volume_status[combo][mode][vtype][index])

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
                for vtype in volumes:
                    diff_volume_stats[combo][mode][vtype] = {}
                    for index in range(len(self.uuids[vtype])):
                        diff_volume_stats[combo][mode][vtype][index] = {}
                        for fkey, fvalue in final_volume_status[combo][mode][vtype][index].items():
                            # Don't compute the difference of stats which is not defined in expected_volume_stats in
                            # the json config file
                            if fkey not in expected_volume_stats[mode][vtype] or fkey == "fault_injection":
                                diff_volume_stats[combo][mode][vtype][index][fkey] = fvalue
                                continue
                            if fkey in initial_volume_status[combo][mode][vtype][index]:
                                ivalue = initial_volume_status[combo][mode][vtype][index][fkey]
                                diff_volume_stats[combo][mode][vtype][index][fkey] = fvalue - ivalue
                        fun_test.log("Difference of {} {} {} volume status before and after the test:".
                                     format(vtype, index, vtype))
                        fun_test.log(diff_volume_stats[combo][mode][vtype][index])

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
                    continue

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

                # Comparing the internal volume stats with the expected value
                for vtype in volumes:
                    for index in range(len(self.uuids[vtype])):
                        for ekey, evalue in expected_volume_stats[mode][vtype].items():
                            if evalue == -1:
                                fun_test.log("Ignoring the {}'s key checking for {} {} volume".format(ekey, vtype,
                                                                                                      index))
                                continue
                            if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
                                if vtype == self.volume_types["ndata"] and index in self.failure_plex_indices:
                                    if ekey == "fault_injection":
                                        evalue = 1
                                    else:
                                        evalue = 0
                                elif self.volume_types["ndata"] != self.volume_types["nparity"] and \
                                        vtype == self.volume_types["nparity"] and (index + self.ec_coding["ndata"]) in \
                                        self.failure_plex_indices:
                                    if ekey == "fault_injection":
                                        evalue = 1
                                    else:
                                        evalue = 0
                            if ekey in diff_volume_stats[combo][mode][vtype][index]:
                                actual = diff_volume_stats[combo][mode][vtype][index][ekey]
                                # row_data_dict[ekey] = actual
                                if actual != evalue:
                                    if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, vtype, index, mode, combo), "PASSED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, vtype, index, evalue))
                                    elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, vtype, index, mode, combo), "PASSED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, vtype, index, evalue))
                                    else:
                                        internal_result[combo][mode] = False
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, vtype, index, mode, combo), "FAILED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is not equal to the "
                                                          "expected value {}".format(ekey, actual, vtype, index, evalue))
                                else:
                                    fun_test.add_checkpoint("{} check for {} {} volume for {} test for the block "
                                                            "size & IO depth combo {}".
                                                            format(ekey, vtype, index, mode, combo), "PASSED",
                                                            evalue, actual)
                                    fun_test.log("Final {} value {} of {} {} volume is equal to the expected value {}".
                                                 format(ekey, actual, vtype, index, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.critical("{} is not found in {} {} volume status".format(ekey, vtype, index))

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
                            fun_test.critical("{} is not found in {} stat".format(ekey, key))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                # post_results("EC with volume level failure domain", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        test_result = True
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)'''

    def cleanup(self):

        '''if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                if index < self.ec_coding["ndata"]:
                    vtype = self.volume_types["ndata"]
                else:
                    vtype = self.volume_types["nparity"]
                    if self.volume_types["ndata"] != self.volume_types["nparity"]:
                        index = index - self.ec_coding["ndata"]
                command_result = self.storage_controller.fail_volume(uuid=self.uuids[vtype][index],
                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disable failure from the {} volume having the UUID "
                                                               "{}".format(vtype, self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=0,
                                              message="Ensuring fault_injection got disabled")'''
        self.command_timeout = 30
        self.ns_id = fun_test.shared_variables["ns_id"]
        self.ec_info = fun_test.shared_variables["ec_info"]
        self.remote_ip = fun_test.shared_variables["remote_ip"]
        # self.ec_coding = fun_test.shared_variables["ec_coding"]  # TODO Remove
        # self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])  # TODO Remove
        # if fun_test.shared_variables[self.ec_ratio]["setup_created"]:

        # Detaching and Unconfiguring all the volumes
        '''command_result = self.storage_controller.volume_detach_pcie(
            ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], command_duration=self.command_timeout)'''
        command_result = self.storage_controller.volume_detach_remote(
            ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], huid=tb_config['dut_info'][0]['huid'],
            ctlid=tb_config['dut_info'][0]['ctlid'], remote_ip=self.remote_ip,
            transport=self.attach_transport, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Detaching LS/EC volume on DUT")

        unconfigure_ec_volume(self.storage_controller,self.ec_info, self.command_timeout)


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
        8. Check the performance for 8k block size
        """)

    def setup(self):
        super(RandReadWrite8kBlocks, self).setup()

    def run(self):
        super(RandReadWrite8kBlocks, self).run()

    def cleanup(self):
        pass
        # super(RandReadWrite8kBlocks, self).cleanup()


if __name__ == "__main__":

    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    ecscript.run()
