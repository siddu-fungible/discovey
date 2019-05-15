from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController

from lib.fun.fs import Fs
from datetime import datetime
import re
from fun_settings import DATA_STORE_DIR

'''
Script to measure performance for a Compression enabled Durable Volume 4:2 EC with Compression Effort Auto 
and Compression Precentages (1%, 50% & 80%).
'''


# Todo Check Requrement of all the routines
def get_ec_vol_cap(num_data_vol, lsv_size):
    return align_8mb(int((lsv_size / num_data_vol) * 1.3)) * num_data_vol


def get_blt_vol_cap(num_data_vol, lsv_size, block_size):
    return align_8mb(int((lsv_size / num_data_vol) * 1.3)) + block_size


def align_8mb(size):
    align_sz = 8 << 20
    return size + int(align_sz - (size % align_sz))


def get_bytes_int(str_size):
    resp = re.search(r'(\d*)([a-zA-Z])', str_size, re.M)
    final_sz = None
    if resp:
        ordinal = int(resp.group(1))
        if resp.group(2) == 'K':
            final_sz = ordinal << 10
        if resp.group(2) == 'M':
            final_sz = ordinal << 20
        if resp.group(2) == 'G':
            final_sz = ordinal << 30
    return final_sz


def get_comp_percent(orig_size, comp_size):
    return ((orig_size - comp_size) / float(orig_size)) * 100


def parse_perf_stats(perf_dict):
    for k in perf_dict:
        if k == "iops" or k == "latency":
            perf_dict[k] = int(round(perf_dict[k]))
        if k == "bw":
            perf_dict[k] = int(round(perf_dict[k] / 1000))
    return perf_dict


VOL_TYPE = "EC_COMP_FS_VOL"


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy F1's.
        2. Depoy End Host.
        3. Launch DPC terminal.
        4. Set Syslog Level to 2(CRIT).
        """)

    def setup(self):

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
            self.reboot_timeout = 300
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        self.fs = topology.get_dut_instance(index=self.f1_in_use)
        self.db_log_time = datetime.now()

        self.come = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip,
                                                    target_port=self.come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
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
        fun_test.shared_variables['ip_configured'] = False
        fun_test.shared_variables['artifacts_shared'] = False

        # Configure Linux Host
        host_up_status = self.end_host.reboot(timeout=self.command_timeout, max_wait_time=self.reboot_timeout)
        fun_test.test_assert(host_up_status, "End Host {} is up".format(self.end_host.host_ip))

        interface_ip_config = "ip addr add {} dev {}".format(self.test_network["test_interface_ip"],
                                                             self.test_interface_name)
        interface_mac_config = "ip link set {} address {}".format(self.test_interface_name,
                                                                  self.test_network["test_interface_mac"])
        link_up_cmd = "ip link set {} up".format(self.test_interface_name)
        static_arp_cmd = "arp -s {} {}".format(self.test_network["test_net_route"]["gw"],
                                               self.test_network["test_net_route"]["arp"])

        self.end_host.sudo_command(command=interface_ip_config,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Configuring test interface IP address")

        self.end_host.sudo_command(command=interface_mac_config,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Assigning MAC to test interface")

        self.end_host.sudo_command(command=link_up_cmd, timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Bringing up test link")

        interface_up_status = self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                             action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                   gateway=self.test_network["test_net_route"]["gw"],
                                   outbound_interface=self.test_interface_name,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Adding route to F1")

        self.end_host.sudo_command(command=static_arp_cmd, timeout=self.command_timeout)
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
            self.storage_controller.disconnect()
            fs = fun_test.shared_variables["fs"]
            fs.cleanup()
        except Exception as ex:
            fun_test.critical(ex.message)


class ECVolumeLevelTestcase(FunTestCase):
    def setup(self):

        testcase = self.__class__.__name__

        # parse benchmark dictionary
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        fun_test.test_assert((testcase in benchmark_dict) or benchmark_dict[testcase],
                             "Test Case: {0} not Present in Benchmark Json: {1}".format(testcase, benchmark_file),
                             ignore_on_success=True)
        # set attr variables
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)
        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        # generate vol_attributes

        # compute BLT, EC vol size
        self.fs = fun_test.shared_variables["fs"]
        self.end_host = fun_test.shared_variables["end_host"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        fun_test.shared_variables["attach_transport"] = self.volume_info['ctrlr']['transport']

        fun_test.shared_variables["ec_coding"] = self.ec_coding
        num_blts = self.ec_coding["ndata"] + self.ec_coding["nparity"]
        if not fun_test.shared_variables['ip_configured']:
            fun_test.test_assert(self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])["status"],
                                 "ip_cfg configured on DUT instance")
            fun_test.shared_variables['ip_configured'] = True

        self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip

        self.vols_created = {}  # dict to record all uuids
        for vtype in self.volume_types:
            self.vols_created[vtype] = []

        self.volume_info["raw"]["capacity"] = get_blt_vol_cap(self.ec_coding["ndata"],
                                                              self.volume_info["lsv"]["capacity"],
                                                              self.volume_info["lsv"]["block_size"])
        self.volume_info["ec"]["capacity"] = get_ec_vol_cap(self.ec_coding["ndata"],
                                                            self.volume_info["lsv"]["capacity"])

        # Create BLT's
        for i in xrange(num_blts):
            raw_vol_uuid = utils.generate_uuid()
            raw_vol_name = "raw_vol_{}".format(i)
            fun_test.test_assert(self.storage_controller.create_volume(type=self.volume_info["raw"]["type"],
                                                                       capacity=self.volume_info["raw"]["capacity"],
                                                                       block_size=self.volume_info["raw"]["block_size"],
                                                                       name=raw_vol_name,
                                                                       uuid=raw_vol_uuid,
                                                                       command_duration=self.command_timeout)['status'],
                                 message="Create BLT volume, uuid: {0}, name: {1}".format(raw_vol_uuid, raw_vol_name))
            self.vols_created["raw"].append({"name": raw_vol_name, "uuid": raw_vol_uuid})
        plex_ids = [x['uuid'] for x in self.vols_created["raw"]]

        # create EC_vol
        ec_vol_name = "ec_vol1"
        ec_vol_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_volume(type=self.volume_info["ec"]["type"],
                                                                   capacity=self.volume_info["ec"]["capacity"],
                                                                   block_size=self.volume_info["ec"]["block_size"],
                                                                   name=ec_vol_name,
                                                                   uuid=ec_vol_uuid,
                                                                   ndata=self.ec_coding["ndata"],
                                                                   nparity=self.ec_coding["nparity"],
                                                                   pvol_id=plex_ids,
                                                                   command_duration=self.command_timeout)['status'],
                             message="Create EC volume, uuid: {0}, name: {1}".format(ec_vol_uuid, ec_vol_name))
        self.vols_created["ec"].append({"name": ec_vol_name, "uuid": ec_vol_uuid})

        # Create jvol
        jvol_name = "jvol1"
        jvol_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_volume(type=self.volume_info["jvol"]["type"],
                                                                   capacity=self.volume_info["jvol"]["capacity"],
                                                                   block_size=self.volume_info["jvol"]["block_size"],
                                                                   name=jvol_name,
                                                                   uuid=jvol_uuid,
                                                                   command_duration=self.command_timeout)['status'],
                             message="Create Journal volume, uuid: {0}, name: {1}".format(jvol_uuid, jvol_name))
        self.vols_created["jvol"].append({"name": jvol_name, "uuid": jvol_uuid})

        # Create required LSV
        lsv_vol_name = "lsv_vol1"
        lsv_vol_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_volume(name=lsv_vol_name,
                                                                   uuid=lsv_vol_uuid,
                                                                   group=self.ec_coding["ndata"],
                                                                   jvol_uuid=jvol_uuid,
                                                                   pvol_id=[ec_vol_uuid],
                                                                   command_duration=self.command_timeout,
                                                                   **self.volume_info['lsv'])['status'],
                             message="Create Lsv volume, uuid: {0}, name: {1}".format(lsv_vol_uuid, lsv_vol_name))
        self.vols_created["lsv"].append({"name": lsv_vol_name, "uuid": lsv_vol_uuid})

        # Create Controller
        fun_test.test_assert(self.storage_controller.volume_attach_remote(
            ns_id=self.volume_info["ctrlr"]["nsid"],
            uuid=lsv_vol_uuid,
            huid=self.volume_info["ctrlr"]["huid"],
            ctlid=self.volume_info["ctrlr"]["ctlid"],
            remote_ip=self.remote_ip,
            transport=self.volume_info["ctrlr"]["transport"],
            command_duration=self.command_timeout)['status'],
                             message="Attach LSV Volume {0} to the Controller".format(lsv_vol_uuid))

        # Disable error injection and verify
        fun_test.test_assert(self.storage_controller.poke(props_tree=["params/ecvol/error_inject", 0],
                                                          legacy=False,
                                                          command_duration=self.command_timeout)['status'],
                             message="Disabling error_injection for EC volume on DUT")
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)

        fun_test.test_assert_expected(
            actual=self.storage_controller.peek(props_tree="params/ecvol", legacy=False)["data"]["error_inject"],
            expected=0,
            message="Error injection variable set",
            ignore_on_success=True)

        # Set Syslog level
        fun_test.test_assert(self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False,
                                                          command_duration=self.command_timeout)["status"],
                             "Setting syslog level to {}".format(self.syslog_level))

        # Checking nvme-connect status
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(
                self.volume_info["ctrlr"]["transport"].lower(),
                self.test_network["f1_loopback_ip"],
                str(self.transport_port),
                self.nvme_subsystem)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                self.volume_info["ctrlr"]["transport"].lower(),
                self.test_network["f1_loopback_ip"],
                str(self.transport_port),
                self.nvme_subsystem,
                str(self.io_queues))

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # Check nvme device is visible to end host
        lsblk_output = self.end_host.lsblk("-b")

        volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(self.volume_info["ctrlr"]["nsid"])
        for volume_name in lsblk_output:
            match = re.search(volume_pattern, volume_name)
            if match:
                self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(
                    self.volume_info["ctrlr"]["nsid"])
                self.volume_name = self.nvme_block_device.replace("/dev/", "")
                fun_test.test_assert_expected(expected=self.volume_name,
                                              actual=lsblk_output[volume_name]["name"],
                                              message="{} device available".format(self.volume_name))
                break
        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
        fun_test.test_assert_expected(expected="disk",
                                      actual=lsblk_output[self.volume_name]["type"],
                                      message="{} device type check".format(self.volume_name))

        # Disable the udev daemon which will skew the read stats of the volume during the test
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            fun_test.test_assert(self.end_host.systemctl(service_name=service,
                                                         action="stop"),
                                 "Stopping {} service".format(service))
        create_fs_resp = self.end_host.create_filesystem(fs_type=self.file_system,
                                                         device=self.nvme_block_device,
                                                         timeout=90)
        fun_test.test_assert(create_fs_resp,
                             message="Create File System on nvme device: {}".format(self.nvme_block_device))

        # create mount dir
        mount_dir = "{0}{1}".format(self.mount_point, testcase)

        fun_test.test_assert(self.end_host.create_directory(dir_name=mount_dir),
                             message="Create Dir {0} for mount".format(mount_dir))
        fun_test.shared_variables['mount_dir'] = mount_dir
        fun_test.test_assert(self.end_host.mount_volume(volume=self.nvme_block_device, directory=mount_dir),
                             message="Mount {0} volume on {1} directory".format(self.nvme_block_device, mount_dir))

        if not fun_test.shared_variables['artifacts_shared']:
            end_host_tmp_dir = "/tmp/"
            for corpus in self.test_corpuses:
                abs_path = "{0}/{1}".format(DATA_STORE_DIR, corpus)
                fun_test.test_assert(os.path.exists(abs_path), message="Check if Dir {} exists".format(abs_path),
                                     ignore_on_success=True)
                fun_test.test_assert(fun_test.scp(source_file_path=abs_path,
                                                  target_file_path=end_host_tmp_dir,
                                                  target_ip=self.end_host.host_ip,
                                                  target_username=self.end_host.ssh_username,
                                                  target_password=self.end_host.ssh_password,
                                                  target_port=self.end_host.ssh_port,
                                                  recursive=True,
                                                  timeout=300),
                                     message="scp dir {} to end host".format(abs_path), ignore_on_success=True)
            fun_test.shared_variables['artifacts_shared'] = True

        # Mount File System on Device

    def flush_cache_mem(self):
        flush_cmd = """sync; echo 1 > /proc/sys/vm/drop_caches; sync; echo 2 > /proc/sys/vm/drop_caches;
        sync; echo 3 > /proc/sys/vm/drop_caches"""
        self.end_host.sudo_command(flush_cmd)

    def run(self):
        mount_dir = fun_test.shared_variables['mount_dir']
        test_corpuses = self.test_corpus
        end_host_tmp_dir = "/tmp/"
        lsv_uuid = self.vols_created['lsv'][0]['uuid']
        self.flush_cache_mem()
        resp = self.storage_controller.peek(props_tree="storage/volumes/{0}".format(
            self.volume_info["lsv"]["type"]))
        fun_test.test_assert(resp, message="Get LSV stats before compression", ignore_on_success=True)
        init_write_count = resp['data'][lsv_uuid]['stats']['write_bytes']

        table_rows = []
        table_header = ["CorpusName", "F1CompressPrecent", "GzipCompressPercent"]
        for corpus in test_corpuses:
            # TOdo check if dir exists
            self.end_host.cp(source_file_name="{}{}".format(end_host_tmp_dir, corpus),
                             destination_file_name=mount_dir, recursive=True, sudo=True),

            self.flush_cache_mem()
            resp = self.storage_controller.peek(props_tree="storage/volumes/{0}".format(
                self.volume_info["lsv"]["type"]))
            fun_test.test_assert(resp, message="Get LSV stats after compression", ignore_on_success=True)
            curr_write_count = resp['data'][lsv_uuid]['stats']['write_bytes']
            comp_size = curr_write_count - init_write_count
            comp_pct = get_comp_percent(orig_size=test_corpuses[corpus]['orig_size'], comp_size=comp_size)
            self.compare_gzip(float(test_corpuses[corpus]['gzip_comp_pct']), float(comp_pct), self.margin, corpus)
            init_write_count = curr_write_count
            table_rows.append([corpus, "{0:04.2f}".format(comp_pct), test_corpuses[corpus]['gzip_comp_pct']])
        fun_test.add_table(panel_header="Compression ratio benchmarking",
                           table_name="Accelerator Effort: {0}, Gizp Effort: {1}".format(self.accelerator_effort,
                                                                                         self.gzip_effort),
                           table_data={"headers": table_header, "rows": table_rows})

    def compare_gzip(self, gzip_percent, accel_percent, margin, file_name):
        diff = accel_percent - gzip_percent
        if diff > 0:
            fun_test.test_assert(diff,
                                 message="FunOS accelerator spacesaving percent {0:04.2f}% higher than gzip space saving percent: {1:04.2f}% for corpus: {2}".format(
                                     accel_percent, gzip_percent, file_name))
        elif (diff < 0):
            fun_test.test_assert(abs(diff) < margin,
                                 message="FunOS accelerator spacesaving percent {0:04.2f}% lesser than gzip space saving percent: {1:04.2f}% within error margin: {2}% for corpus: {3}".format(
                                     accel_percent, gzip_percent, margin, file_name))

    def cleanup(self):
        try:
            # Do nvme disconnect
            cmd = "sudo nvme disconnect -n {0} -d {1}".format(self.nvme_subsystem, self.volume_name)
            self.end_host.sudo_command(cmd)
            
            # Detach LSV from Controller
            lsv_uuid = self.vols_created['lsv'][0]['uuid']
            lsv_name = self.vols_created['lsv'][0]['name']
            jvol_uuid = self.vols_created['jvol'][0]['uuid']
            jvol_name = self.vols_created['jvol'][0]['name']
            ec_uuid = self.vols_created['ec'][0]['uuid']
            ec_name = self.vols_created['ec'][0]['name']
            plex_ids = [x['uuid'] for x in self.vols_created["raw"]]
            num_blts = self.ec_coding["ndata"] + self.ec_coding["nparity"]
            # Todo Delete the controller when implementation is done
            self.storage_controller.volume_detach_pcie(ns_id=self.volume_info['ctrlr']['nsid'],
                                                       uuid=lsv_uuid,
                                                       huid=self.volume_info["ctrlr"]["huid"],
                                                       ctlid=self.volume_info["ctrlr"]["ctlid"],
                                                       command_duration=self.command_timeout)

            # Delete LSV Volume
            self.storage_controller.delete_volume(name=lsv_name,
                                                  uuid=lsv_uuid,
                                                  group=self.ec_coding["ndata"],
                                                  jvol_uuid=jvol_uuid,
                                                  pvol_id=[ec_uuid],
                                                  command_duration=self.command_timeout,
                                                  **self.volume_info['lsv'])
            # Delete the Jvol
            self.storage_controller.delete_volume(type=self.volume_info["jvol"]["type"],
                                                  capacity=self.volume_info["jvol"]["capacity"],
                                                  block_size=self.volume_info["jvol"]["block_size"],
                                                  name=jvol_name,
                                                  uuid=jvol_uuid,
                                                  command_duration=self.command_timeout)
            # Delete the EC vol
            self.storage_controller.delete_volume(type=self.volume_info["ec"]["type"],
                                                  capacity=self.volume_info["ec"]["capacity"],
                                                  block_size=self.volume_info["ec"]["block_size"],
                                                  name=ec_name,
                                                  uuid=ec_uuid,
                                                  ndata=self.ec_coding["ndata"],
                                                  nparity=self.ec_coding["nparity"],
                                                  pvol_id=plex_ids,
                                                  command_duration=self.command_timeout)
            # Delete all blt vols.
            for i in xrange(num_blts):
                blt_name = self.vols_created['raw'][i]['name']
                blt_uuid = self.vols_created['raw'][i]['uuid']
                self.storage_controller.delete_volume(type=self.volume_info["raw"]["type"],
                                                      capacity=self.volume_info["raw"]["capacity"],
                                                      block_size=self.volume_info["raw"]["block_size"],
                                                      name=blt_name,
                                                      uuid=blt_uuid,
                                                      command_duration=self.command_timeout)

        except Exception as ex:
            fun_test.critical(ex.message)


class EcCompBenchmarkEffortAuto(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Compression ratio's for different corpus's of data with F1's compression"
                                      " engine and compare it with Gzip. F1 Effort: Auto, Gzip Effort: 6",
                              steps="""
                              1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                                 a Journal Volume and an LSV volume with compression enabled effort Auto.
                              2. Attach LSV volume to the nvme controller.  
                              3. Create file system on the attached device and mount it with a directory.
                              4. Capture write count before copying data to mount point and after copying it.
                              5. Compute percentage space savings and compare it with that achieved using gzip
                              """)

    def setup(self):
        super(EcCompBenchmarkEffortAuto, self).setup()

    def run(self):
        super(EcCompBenchmarkEffortAuto, self).run()

    def cleanup(self):
        super(EcCompBenchmarkEffortAuto, self).cleanup()


class EcCompBenchmarkEffort64Gbps(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Compression ratio's for different corpus's of data with F1's compression"
                                      " engine and compare it with Gzip. F1 Effort: 64Gbps, Gzip Effort: 1",
                              steps="""
                              1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                                 a Journal Volume and an LSV volume with compression enabled effort Auto.
                              2. Attach LSV volume to the nvme controller.  
                              3. Create file system on the attached device and mount it with a directory.
                              4. Capture write count before copying data to mount point and after copying it.
                              5. Compute percentage space savings and compare it with that achieved using gzip
                              """)

    def setup(self):
        super(EcCompBenchmarkEffort64Gbps, self).setup()

    def run(self):
        super(EcCompBenchmarkEffort64Gbps, self).run()

    def cleanup(self):
        super(EcCompBenchmarkEffort64Gbps, self).cleanup()


class EcCompBenchmarkEffort2Gbps(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Compression ratio's for different corpus's of data with F1's compression"
                                      " engine and compare it with Gzip. F1 Effort: 2Gbps, Gzip Effort: 9",
                              steps="""
                              1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                                 a Journal Volume and an LSV volume with compression enabled effort Auto.
                              2. Attach LSV volume to the nvme controller.  
                              3. Create file system on the attached device and mount it with a directory.
                              4. Capture write count before copying data to mount point and after copying it.
                              5. Compute percentage space savings and compare it with that achieved using gzip
                              """)

    def setup(self):
        super(EcCompBenchmarkEffort2Gbps, self).setup()

    def run(self):
        super(EcCompBenchmarkEffort2Gbps, self).run()

    def cleanup(self):
        super(EcCompBenchmarkEffort2Gbps, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EcCompBenchmarkEffortAuto())
    ecscript.add_test_case(EcCompBenchmarkEffort64Gbps())
    ecscript.add_test_case(EcCompBenchmarkEffort2Gbps())
    init_time = time.time()
    ecscript.run()
    fun_test.add_checkpoint("Script Run time: {}", time.time() - init_time)
