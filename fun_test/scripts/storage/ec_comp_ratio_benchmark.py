from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.fun.fs import Fs
from storage_helper import *
from fun_settings import DATA_STORE_DIR
from fun_global import PerfUnit, is_production_mode
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
import copy

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


def get_comp_ratio(orig_size, comp_size):
    return orig_size / float(comp_size)


def get_lsv_write_count(storage_controller, lsv_uuid):
    lsv_keyword = "VOL_TYPE_BLK_LSV"
    resp = storage_controller.peek(props_tree="storage/volumes/{0}/{1}".format(lsv_keyword, lsv_uuid))
    fun_test.test_assert(resp['status'], message="Get LSV stats before compression", ignore_on_success=True)
    return resp['data']['stats']['write_bytes']


class ECVolumeLevelScript(FunTestScript):
    ctrlr_uuid = None
    storage_controller = None
    end_host = None

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
            self.command_timeout = 30
            self.reboot_timeout = 540
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))
        testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0,
                                           custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "FS Topology deployed")

        fs = topology.get_dut_instance(index=0)
        come = fs.get_come()
        self.storage_controller = StorageController(target_ip=come.host_ip,
                                                    target_port=come.get_dpc_port(self.f1_in_use))
        if not check_come_health(self.storage_controller):
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology re-deployed")
            come = topology.get_dut_instance(index=0).get_come()
            self.storage_controller = StorageController(target_ip=come.host_ip,
                                                        target_port=come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0,
                                                                            f1_index=self.f1_in_use)
        test_interface_name = None
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if testbed_type == "fs-6" and host_ip != "poc-server-01":  # TODO temp check for FS6 should be removed
                continue
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                self.end_host = host_info["host_obj"]
                test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(fpg_inteface_index))
                break
        else:
            fun_test.test_assert(False, "Host found with Test Interface")

        test_network = self.csr_network[str(fpg_inteface_index)]
        remote_ip = test_network["test_interface_ip"].split('/')[0]
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables['date_time'] = get_data_collection_time()

        # Configure Linux Host
        fun_test.test_assert(self.end_host.reboot(timeout=self.command_timeout,
                                                  max_wait_time=self.reboot_timeout),
                             "End Host {} is up".format(self.end_host.host_ip))

        configure_endhost_interface(end_host=self.end_host,
                                    test_network=test_network,
                                    interface_name=test_interface_name)

        # Loading the nvme and nvme_tcp modules
        load_nvme_module(self.end_host)
        load_nvme_tcp_module(self.end_host)

        # config ip
        configure_fs_ip(self.storage_controller, test_network["f1_loopback_ip"])

        # create controller
        self.ctrlr_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                       transport=self.attach_transport,
                                                                       remote_ip=remote_ip,
                                                                       nqn=self.nvme_subsystem,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)['status'],
                             message="Create Storage Controller for {} with controller uuid {} on DUT".format(
                                 self.attach_transport, self.ctrlr_uuid))

        # create EC Volumes
        configured_vols = {}  # dict to keep tab on ec vols created
        ns_id = 1
        fun_test.shared_variables['configured_vols'] = configured_vols
        for effort in self.zip_effort_list:
            self.ec_info["zip_effort"] = effort
            (ec_config_status, ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                      self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume with zip effort: {}".format(effort))
            lsv_uuid = ec_info["attach_uuid"][0]
            configured_vols[effort] = {'ns_id': ns_id,
                                       'lsv_uuid': lsv_uuid,
                                       'capacity': ec_info["volume_capacity"][0]["lsv"]}
            configured_vols[effort]['ec_info'] = copy.deepcopy(ec_info)

            fun_test.test_assert(self.storage_controller.attach_volume_to_controller(
                ctrlr_uuid=self.ctrlr_uuid,
                ns_id=ns_id,
                vol_uuid=lsv_uuid,
                command_duration=self.command_timeout)["status"],
                                 message="Attach EC/LS volume with nsid: {} to controller with uuid: {}".format(
                                     ns_id,
                                     self.ctrlr_uuid))
            ns_id += 1
            self.ec_info["capacity"] += 1 << 30  # additional param to identify vol ids

        # disable error injection for ec-volumes
        disable_error_inject(self.storage_controller, self.command_timeout)

        # execute nvme-connect
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                             test_network["f1_loopback_ip"],
                                                                             self.transport_port,
                                                                             self.nvme_subsystem)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                self.attach_transport.lower(),
                test_network["f1_loopback_ip"],
                self.transport_port,
                self.nvme_subsystem,
                self.io_queues)

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # Check all devices are visible and mount them on end host
        for effort in configured_vols:
            ns_id = configured_vols[effort]['ns_id']
            fetch_nvme = fetch_nvme_device(self.end_host, ns_id, configured_vols[effort]['capacity'])
            fun_test.test_assert(fetch_nvme['status'], message="Check nvme device visible on end host")
            configured_vols[effort]['volume_name'] = fetch_nvme['volume_name']
            configured_vols[effort]['nvme_device'] = fetch_nvme['nvme_device']

            # Create file system on attached device
            for i in xrange(2):  # Try mkfs twice first time it might fail due to crash in nvme device
                try:
                    resp = self.end_host.create_filesystem(fs_type=self.file_system,
                                                           device=fetch_nvme['nvme_device'],
                                                           timeout=210)
                    if resp:
                        break
                    else:
                        fun_test.sleep(
                            message="mkfs failed on first attempt for device: {} ".format(fetch_nvme['nvme_device']),
                            seconds=15)
                except Exception as ex:
                    fun_test.critical(ex.message)
            fun_test.test_assert(resp,
                                 message="Create File System on nvme device: {}".format(fetch_nvme['nvme_device']))

            # create mount dir for respective volumes
            mount_dir = "{0}{1}".format(self.mount_point, effort)
            fun_test.test_assert(self.end_host.create_directory(dir_name=mount_dir),
                                 message="Create Dir {0} to mount volume {1}".format(mount_dir,
                                                                                     fetch_nvme['volume_name']))
            configured_vols[effort]['mount_point'] = mount_dir

            # mount volume on end host
            fun_test.test_assert(self.end_host.mount_volume(volume=fetch_nvme['nvme_device'], directory=mount_dir),
                                 message="Mount {0} volume on {1} directory".format(fetch_nvme['nvme_device'],
                                                                                    mount_dir))

        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            fun_test.test_assert(self.end_host.systemctl(service_name=service,
                                                         action="stop"),
                                 "Stopping {} service".format(service))

        end_host_tmp_dir = "/tmp/"
        for corpus in self.corpus_list:
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
        fun_test.shared_variables['configured_vols'] = configured_vols

    def cleanup(self):
        try:
            # add syslogs
            host_syslog_path = "/var/log/syslog"
            syslog_file = fun_test.get_test_case_artifact_file_name(post_fix_name="end_host_syslog.txt")
            fun_test.scp(source_file_path=host_syslog_path,
                         target_file_path=syslog_file,
                         source_ip=self.end_host.host_ip,
                         source_username=self.end_host.ssh_username,
                         source_password=self.end_host.ssh_password,
                         source_port=self.end_host.ssh_port)
            fun_test.add_auxillary_file(description="Host Machine Syslogs", filename=syslog_file)
            if 'configured_vols' in fun_test.shared_variables and fun_test.shared_variables['configured_vols']:
                configured_vols = fun_test.shared_variables['configured_vols']
                for effort in configured_vols:
                    # Unmount Volume
                    self.end_host.unmount_volume(volume=configured_vols[effort]['nvme_device'])
                    # execute nvme disconnect
                    self.end_host.sudo_command("nvme disconnect -d {}".format(configured_vols[effort]['volume_name']))
                    # detach volume from controller
                    fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid,
                        ns_id=configured_vols[effort]['ns_id'],
                        command_duration=self.command_timeout)['status'],
                                         message="Detach nsid: {} from controller: {}".format(
                                             configured_vols[effort]['ns_id'], self.ctrlr_uuid))
                    # delete the volumes
                    self.storage_controller.unconfigure_ec_volume(ec_info=configured_vols[effort]['ec_info'],
                                                                  command_timeout=self.command_timeout)

            # delete the controller
            if self.ctrlr_uuid:
                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(self.ctrlr_uuid))
            self.storage_controller.disconnect()
        except Exception as ex:
            fun_test.critical(ex.message)
        finally:
            fun_test.shared_variables["topology"].cleanup()


class ECVolumeLevelTestcase(FunTestCase):
    def setup(self):
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        fun_test.test_assert((testcase in benchmark_dict) or benchmark_dict[testcase],
                             "Test Case: {0} not Present in Benchmark Json: {1}".format(testcase, benchmark_file),
                             ignore_on_success=True)
        # set attr variables
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        fun_test.simple_assert(self.accelerator_effort in fun_test.shared_variables['configured_vols'],
                               message="Check vol info for the respective test case is present")
        test_case_info = fun_test.shared_variables['configured_vols'][self.accelerator_effort]
        storage_controller = fun_test.shared_variables["storage_controller"]
        end_host = fun_test.shared_variables["end_host"]
        mount_dir = test_case_info['mount_point']
        test_corpuses = self.test_corpus
        end_host_tmp_dir = "/tmp/"
        lsv_uuid = test_case_info['lsv_uuid']

        end_host.flush_cache_mem(timeout=200)
        init_write_count = get_lsv_write_count(storage_controller, lsv_uuid)

        table_rows = []
        post_result_lst = []
        table_header = ["CorpusName", "F1CompressPrecent", "GzipCompressPercent"]
        test_result = True
        for corpus in test_corpuses:
            end_host.cp(source_file_name="{}{}".format(end_host_tmp_dir, corpus),
                        destination_file_name=mount_dir, recursive=True, sudo=True),
            corpus_dest_path = "{}/{}".format(mount_dir, corpus)
            fun_test.test_assert(end_host.check_file_directory_exists(corpus_dest_path),
                                 message="Check corpus got copied to mount dir",
                                 ignore_on_success=True)
            end_host.flush_cache_mem(timeout=200)

            curr_write_count = get_lsv_write_count(storage_controller, lsv_uuid)
            comp_size = curr_write_count - init_write_count
            fun_test.simple_assert(comp_size, "Check compressed size is non-zero value")
            comp_ratio = get_comp_ratio(orig_size=test_corpuses[corpus]['orig_size'], comp_size=comp_size)
            # gzip_float_pct = float(test_corpuses[corpus]['gzip_comp_pct'])
            # compare_result, diff = compare_gzip(gzip_float_pct, comp_ratio, self.margin)
            '''fun_test.add_checkpoint("FunOS accelerator spacesaving percentage {0:04.2f}% {1} than gzip space"
                                    "saving percentage: {2:04.2f}% for corpus: {3}".format(comp_ratio,
                                                                                           "GREATER" if compare_result
                                                                                           else "LESSER",
                                                                                           gzip_float_pct,
                                                                                           corpus))'''
            fun_test.add_checkpoint("FunOS accelerator compression-ratio: {0:04.2f}%, compressed size: {1}"
                                    " for corpus: {2}".format(comp_ratio, comp_size, corpus))

            post_result_lst.append({'effort_name': self.accelerator_effort,
                                    'corpus_name': corpus,
                                    'f1_compression_ratio': comp_ratio,
                                    'date_time': fun_test.shared_variables['date_time']})
            init_write_count = curr_write_count
            table_rows.append([corpus, "{0:04.2f}".format(comp_ratio), test_corpuses[corpus]['gzip_comp_ratio']])
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
        fun_test.log(result_lst)
        try:
            for d in result_lst:
                generic_helper = ModelHelper(model_name="InspurZipCompressionRatiosPerformance")
                generic_helper.set_units(**unit_dict)
                generic_helper.add_entry(**d)
                generic_helper.set_status(fun_test.PASSED)
                fun_test.log("Result posted to database: {}".format(d))
        except Exception as ex:
            fun_test.critical(ex.message)

    def cleanup(self):
        pass


class EcCompBenchmarkEffort7Gbps(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.13.1 Test Compression ratio's for different corpus's of data with "
                                      "F1's compression engine and compare it with Gzip. F1 Effort: 7Gbps, Gzip Effort: 6",
                              steps="""
                          1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                             a Journal Volume and an LSV volume with compression enabled effort 7Gbps.
                          2. Attach LSV volume to the nvme controller.  
                          3. Create file system on the attached device and mount it with a directory.
                          4. Capture write count before copying data to mount point and after copying it.
                          5. Compute percentage space savings and compare it with that achieved using gzip
                          """)

    def setup(self):
        super(EcCompBenchmarkEffort7Gbps, self).setup()

    def run(self):
        super(EcCompBenchmarkEffort7Gbps, self).run()

    def cleanup(self):
        super(EcCompBenchmarkEffort7Gbps, self).cleanup()


class EcCompBenchmarkEffort64Gbps(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.13.1 Test Compression ratio's for different corpus's of data with "
                                      "F1's compression engine and compare it with Gzip. F1 Effort: 64Gbps, Gzip Effort: 1",
                              steps="""
                          1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                             a Journal Volume and an LSV volume with compression enabled effort 64Gbps.
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
                             a Journal Volume and an LSV volume with compression enabled effort 2Gbps.
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
    ecscript.add_test_case(EcCompBenchmarkEffort7Gbps())
    ecscript.add_test_case(EcCompBenchmarkEffort64Gbps())
    ecscript.add_test_case(EcCompBenchmarkEffort2Gbps())
    init_time = time.time()
    ecscript.run()
