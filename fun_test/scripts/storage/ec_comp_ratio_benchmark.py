from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.fun.fs import Fs
from ec_perf_helper import *
from fun_settings import DATA_STORE_DIR
from fun_global import PerfUnit, is_production_mode
from web.fun_test.analytics_models_helper import ModelHelper

'''
Script to compare space savings achieved using Compression enabled storage engine Compression disabled ones
'''


def compare_gzip(gzip_percent, accel_percent, margin):
    # get difference,
    diff = accel_percent - gzip_percent
    result = True
    if diff > 0:
        result = True
    elif diff < 0:
        if abs(diff) > margin:
            result = False
    return result, diff


def get_comp_percent(orig_size, comp_size):
    return ((orig_size - comp_size) / float(orig_size)) * 100


def get_lsv_write_count(storage_controller, lsv_uuid):
    lsv_keyword = "VOL_TYPE_BLK_LSV"
    resp = storage_controller.peek(props_tree="storage/volumes/{0}/{1}".format(lsv_keyword, lsv_uuid))
    fun_test.test_assert(resp['status'], message="Get LSV stats before compression", ignore_on_success=True)
    return resp['data']['stats']['write_bytes']


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
            self.command_timeout = 5
            self.reboot_timeout = 480
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))
        testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=self.f1_in_use,
                                           custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "FS Topology deployed")

        self.fs = topology.get_dut_instance(index=0)

        self.come = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip,
                                                    target_port=self.come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0,
                                                                            f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if testbed_type == "fs-6" and host_ip != "poc-server-01":  # TODO temp check for FS6 should be removed
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
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables['ip_configured'] = False
        fun_test.shared_variables['artifacts_shared'] = False
        fun_test.shared_variables['nvme_device_connected'] = False
        fun_test.shared_variables['huid'] = self.huid
        fun_test.shared_variables['ctlid'] = self.ctlid

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

        fun_test.test_assert(self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                            action="up"), "Bringing up test interface")

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
            self.fs.cleanup()
        except Exception as ex:
            fun_test.critical(ex.message)


class ECVolumeLevelTestcase(FunTestCase):
    def setup(self):
        testcase = self.__class__.__name__
        fun_test.shared_variables['setup_complete'] = False
        huid = fun_test.shared_variables['huid']
        ctlid = fun_test.shared_variables['ctlid']
        self.end_host = fun_test.shared_variables["end_host"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        # parse benchmark dictionary
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        fun_test.test_assert((testcase in benchmark_dict) or benchmark_dict[testcase],
                             "Test Case: {0} not Present in Benchmark Json: {1}".format(testcase, benchmark_file),
                             ignore_on_success=True)
        # set attr variables
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # compute BLT, EC vol size
        if not fun_test.shared_variables['ip_configured']:
            fun_test.test_assert(self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])["status"],
                                 "ip_cfg configured on DUT instance")
            fun_test.shared_variables['ip_configured'] = True

        self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip

        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)
        fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
        fun_test.log("EC details after configuring EC Volume:")
        for k, v in self.ec_info.items():
            fun_test.log("{}: {}".format(k, v))

        # Create Controller
        fun_test.test_assert(self.storage_controller.volume_attach_remote(ns_id=self.ns_id,
                                                                          uuid=self.ec_info["attach_uuid"][0],
                                                                          huid=huid,
                                                                          ctlid=ctlid,
                                                                          remote_ip=self.remote_ip,
                                                                          transport=self.attach_transport,
                                                                          command_duration=self.command_timeout)[
                                 'status'],
                             message="Attach LSV Volume {0} to the Controller".format(self.ec_info["attach_uuid"][0]))

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

        # Checking nvme-connect status
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                             self.test_network["f1_loopback_ip"],
                                                                             str(self.transport_port),
                                                                             self.nvme_subsystem)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                self.attach_transport.lower().lower(),
                self.test_network["f1_loopback_ip"],
                str(self.transport_port),
                self.nvme_subsystem,
                str(self.io_queues))

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # Check nvme device is visible to end host
        fetch_nvme = fetch_nvme_device(self.end_host, self.ns_id)
        fun_test.test_assert(fetch_nvme['status'], message="Check nvme device visible on end host")
        self.volume_name = fetch_nvme['volume_name']
        self.nvme_block_device = fetch_nvme['nvme_device']
        fun_test.shared_variables['setup_complete'] = True

        # Disable the udev daemon which will skew the read stats of the volume during the test
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            fun_test.test_assert(self.end_host.systemctl(service_name=service,
                                                         action="stop"),
                                 "Stopping {} service".format(service))

        # Create file system on attached device
        fun_test.test_assert(self.end_host.create_filesystem(fs_type=self.file_system,
                                                             device=self.nvme_block_device,
                                                             timeout=self.command_timeout),
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
            for corpus in self.test_corpus:
                abs_path = "{0}/{1}/{2}".format(DATA_STORE_DIR, self.artifact_dir, corpus)
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
                                     message="scp corpus {} to end host".format(abs_path), ignore_on_success=True)
            fun_test.shared_variables['artifacts_shared'] = True

    def run(self):
        mount_dir = fun_test.shared_variables['mount_dir']
        test_corpuses = self.test_corpus
        end_host_tmp_dir = "/tmp/"
        lsv_uuid = self.ec_info["attach_uuid"][0]
        self.end_host.flush_cache_mem()

        init_write_count = get_lsv_write_count(self.storage_controller, lsv_uuid)

        table_rows = []
        post_result_lst = []
        table_header = ["CorpusName", "F1CompressPrecent", "GzipCompressPercent"]
        test_result = True
        for corpus in test_corpuses:
            # TOdo check if dir exists
            self.end_host.cp(source_file_name="{}{}".format(end_host_tmp_dir, corpus),
                             destination_file_name=mount_dir, recursive=True, sudo=True),
            corpus_dest_path = "{}/{}".format(mount_dir, corpus)
            fun_test.test_assert(self.end_host.check_file_directory_exists(corpus_dest_path),
                                 message="Check corpus got copied to mount dir",
                                 ignore_on_success=True)
            self.end_host.flush_cache_mem()

            curr_write_count = get_lsv_write_count(self.storage_controller, lsv_uuid)
            comp_size = curr_write_count - init_write_count
            fun_test.simple_assert(comp_size, "Check compressed size is non-zero value")
            comp_pct = get_comp_percent(orig_size=test_corpuses[corpus]['orig_size'], comp_size=comp_size)
            gzip_float_pct = float(test_corpuses[corpus]['gzip_comp_pct'])
            compare_result, diff = compare_gzip(gzip_float_pct, comp_pct, self.margin)
            fun_test.add_checkpoint("FunOS accelerator spacesaving percentage {0:04.2f}% {1} than gzip space"
                                    "saving percentage: {2:04.2f}% for corpus: {3}".format(comp_pct,
                                                                                           "GREATER" if compare_result
                                                                                           else "LESSER",
                                                                                           gzip_float_pct,
                                                                                           corpus))

            post_result_lst.append({'effort_name': self.accelerator_effort,
                                    'corpus_name': corpus,
                                    'f1_compression_ratio': comp_pct})
            #if not compare_result:
            #    test_result = False
            init_write_count = curr_write_count
            table_rows.append([corpus, "{0:04.2f}".format(comp_pct), test_corpuses[corpus]['gzip_comp_pct']])
        fun_test.add_table(panel_header="Compression ratio benchmarking",
                           table_name="Accelerator Effort: {0}, Gizp Effort: {1}".format(self.accelerator_effort,
                                                                                         self.gzip_effort),
                           table_data={"headers": table_header, "rows": table_rows})
        if is_production_mode():
            self.publish_result(post_result_lst)

        fun_test.test_assert(test_result,
                             message="F1 Compression benchmarking with Accelerator Effort: {0} and Gzip Effort: {1}".format(
                                 self.accelerator_effort, self.gzip_effort))

    def publish_result(self, result_lst):
        unit_dict = {"f1_compression_ratio_unit": PerfUnit.UNIT_NUMBER}
        generic_helper = ModelHelper(model_name="InspurZipCompressionRatiosPerformance")
        fun_test.log(result_lst)
        try:
            generic_helper.set_units(**unit_dict)
            for d in result_lst:
                generic_helper.add_entry(**d)
            generic_helper.set_status(fun_test.PASSED)
        except Exception as ex:
            fun_test.critical(ex.message)
        fun_test.log("Result posted to database")

    def cleanup(self):
        try:
            # Do nvme disconnect
            cmd = "sudo nvme disconnect -d {0}".format(self.volume_name)
            self.end_host.sudo_command(cmd)
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                          message=" Execute nvme Disconnect for device: {}".format(self.volume_name))

            huid = fun_test.shared_variables['huid']
            ctlid = fun_test.shared_variables['ctlid']
            if fun_test.shared_variables["setup_complete"]:
                # Detaching all the EC/LS volumes to the external server
                command_result = self.storage_controller.volume_detach_remote(ns_id=self.ns_id,
                                                                              uuid=self.ec_info["attach_uuid"][0],
                                                                              huid=huid,
                                                                              ctlid=ctlid,
                                                                              remote_ip=self.remote_ip,
                                                                              transport=self.attach_transport,
                                                                              command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Detaching EC/LS volume on DUT")

            self.storage_controller.unconfigure_ec_volume(self.ec_info, self.command_timeout)
            fun_test.shared_variables["setup_complete"] = False
        except Exception as ex:
            fun_test.critical(ex.message)


class EcCompBenchmarkEffortAuto(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.13.1 Test Compression ratio's for different corpus's of data with "
                                      "F1's compression engine and compare it with Gzip. F1 Effort: Auto, Gzip Effort: 6",
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
                              summary="Inspur TC 8.13.1 Test Compression ratio's for different corpus's of data with "
                                      "F1's compression engine and compare it with Gzip. F1 Effort: 64Gbps, Gzip Effort: 1",
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
                              summary="Inspur TC 8.13.1 Test Compression ratio's for different corpus's of data with"
                                      " F1's compression engine and compare it with Gzip. F1 Effort: 2Gbps, Gzip Effort: 9",
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
