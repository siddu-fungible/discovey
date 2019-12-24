from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.fun.fs import Fs
from scripts.storage.storage_helper import *
from lib.host.linux import Linux

'''
Sanity Script for BLT Volume via NVME/TCP
Dependency: The script is tightly coupled with fs-6 and poc-server-01, while porting please take care of them.
'''


class BLTVolumeSanityScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Setup COMe, launch DPC cli
        3. 
        """)

    def setup(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        testbed_type = fun_test.get_job_environment_variable("test_bed_type")

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 6
            self.command_timeout = 5
            self.reboot_timeout = 300
            self.end_host_name = "poc-server-01"
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        host_spec = fun_test.get_asset_manager().get_host_spec(name=self.end_host_name)
        host_obj = Linux(**host_spec)
        host_obj.reboot(non_blocking=True)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        fs = topology.get_dut_instance(index=0)
        come = fs.get_come()
        storage_controller = StorageController(target_ip=come.host_ip,
                                               target_port=come.get_dpc_port(self.f1_in_use))

        end_host = None
        test_interface_name = None
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                if testbed_type == "fs-6" and host_ip != self.end_host_name:
                    continue
                end_host = host_info["host_obj"]
                test_interface_name = end_host.extra_attributes["test_interface_name"]
                fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(fpg_inteface_index))
                break
        else:
            fun_test.test_assert(end_host, "Fetch host with required test interface for configuration")

        test_network = self.csr_network[str(fpg_inteface_index)]
        remote_ip = test_network["test_interface_ip"].split('/')[0]

        fun_test.shared_variables["end_host"] = end_host
        fun_test.shared_variables["test_network"] = test_network
        fun_test.shared_variables["storage_controller"] = storage_controller
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables['topology'] = topology
        self.end_host = end_host
        self.storage_controller = storage_controller

        # configure end host
        # reboot host
        fun_test.test_assert(end_host.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                             "End Host {} is up".format(end_host.host_ip))

        # end host network interface
        configure_endhost_interface(end_host=end_host, test_network=test_network,
                                    interface_name=test_interface_name)

        # load nvme
        load_nvme_module(end_host)
        # load nvme_tcp
        load_nvme_tcp_module(end_host)

        # enable_counters(storage_controller, self.command_timeout)

        # configure ip on fs
        fun_test.test_assert(storage_controller.ip_cfg(ip=test_network['f1_loopback_ip'])["status"],
                             "Configure IP {} on FS".format(test_network['f1_loopback_ip']))

        # create controller
        ctrlr_uuid = utils.generate_uuid()
        fun_test.test_assert(storage_controller.create_controller(ctrlr_id=0,
                                                                  ctrlr_uuid=ctrlr_uuid,
                                                                  ctrlr_type="BLOCK",
                                                                  transport=self.attach_transport,
                                                                  remote_ip=remote_ip,
                                                                  subsys_nqn=self.nvme_subsystem,
                                                                  host_nqn=remote_ip,
                                                                  port=self.transport_port,
                                                                  command_duration=self.command_timeout)["status"],
                             "Create Storage Controller for {} with controller uuid {} on DUT".
                             format(self.attach_transport, ctrlr_uuid))
        fun_test.shared_variables["ctrlr_uuid"] = ctrlr_uuid

        # Create thin BLT volume
        blt_uuid = utils.generate_uuid()
        command_result = storage_controller.create_thin_block_volume(capacity=self.blt_details["capacity"],
                                                                     block_size=self.blt_details["block_size"],
                                                                     name=self.blt_details['name'],
                                                                     uuid=blt_uuid,
                                                                     command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(
            self.blt_details['name'],
            blt_uuid))

        # attach volume to controller
        fun_test.test_assert(self.storage_controller.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=blt_uuid)["status"],
                             "Attaching BLT {} with uuid {} to controller".format(self.ns_id, blt_uuid))
        fun_test.shared_variables["blt_uuid"] = blt_uuid

        # Set syslog level
        set_syslog_level(storage_controller, fun_test.shared_variables['syslog_level'])

        # execute nvme connect
        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                         test_network["f1_loopback_ip"],
                                                                         self.transport_port,
                                                                         self.nvme_subsystem)
        if hasattr(self, "io_queues") and self.io_queues:
            nvme_connect_cmd += " -i {}".format(self.io_queues)

        nvme_connect_status = end_host.sudo_command(command=nvme_connect_cmd, timeout=60)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # check nvme device is visible on end host
        fetch_nvme = fetch_nvme_device(end_host, self.ns_id)
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
        fun_test.shared_variables['nvme_block_device'] = fetch_nvme['nvme_device']
        fun_test.shared_variables['volume_name'] = fetch_nvme['volume_name']

        # execute fio write to populate device
        if self.warm_up_traffic:
            fio_output = self.end_host.pcie_fio(filename=fun_test.shared_variables['nvme_block_device'],
                                                **self.warm_up_fio_cmd_args)
            fun_test.test_assert(fio_output, "Pre-populating the volume")
        fun_test.shared_variables["setup_created"] = True
        fun_test.shared_variables["blt_details"] = self.blt_details

    def cleanup(self):
        try:
            if fun_test.shared_variables['setup_created']:
                ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                blt_uuid = fun_test.shared_variables["blt_uuid"]
                self.end_host.sudo_command("nvme disconnect -d {}".format(fun_test.shared_variables['volume_name']))

                # disconnect device from controller
                fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=ctrlr_uuid,
                    ns_id=self.ns_id,
                    command_duration=self.command_timeout)['status'],
                                     message="Detach nsid: {} from controller: {}".format(self.ns_id, ctrlr_uuid))

                # delete controller
                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(ctrlr_uuid))
                fun_test.sleep(seconds=1, message="BLT volume detached from controller")
                # delete BLT
                fun_test.test_assert(self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           type=self.blt_details["type"],
                                                                           name=self.blt_details["name"],
                                                                           uuid=blt_uuid,
                                                                           command_duration=self.command_timeout)
                                     ['status'],
                                     message="Delete Configured BLT")
        except Exception as ex:
            fun_test.critical(ex.message)
        finally:
            self.storage_controller.disconnect()
            fun_test.shared_variables["topology"].cleanup()


class BltTcpSanityTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        testcase = self.__class__.__name__
        self.test_mode = testcase[6:].lower()

        self.blt_details = fun_test.shared_variables["blt_details"]
        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[self.blt_details["type"]] = [fun_test.shared_variables["blt_uuid"]]
        vol_details.append(vol_group)

        self.storage_controller = fun_test.shared_variables["storage_controller"]

        mode = self.fio_mode
        end_host = fun_test.shared_variables["end_host"]
        nvme_block_device = fun_test.shared_variables['nvme_block_device']
        fio_numjob_iodepths = self.fio_numjobs_iodepth
        fun_test.simple_assert(nvme_block_device, "nvme block device available for test")
        for combo in fio_numjob_iodepths:
            num_jobs, iodepth = eval(combo)

            # Starting stats collection
            file_suffix = "{}_iodepth_{}.txt".format(self.test_mode, (int(iodepth) * int(num_jobs)))
            for index, stat_detail in enumerate(self.stats_collect_details):
                func = stat_detail.keys()[0]
                self.stats_collect_details[index][func]["count"] = int(
                    self.fio_cmd_args["runtime"] / self.stats_collect_details[index][func]["interval"])
                if func == "vol_stats":
                    self.stats_collect_details[index][func]["vol_details"] = vol_details
            fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format((int(iodepth) * int(num_jobs)), self.stats_collect_details))
            self.storage_controller.verbose = False
            stats_obj = CollectStats(self.storage_controller)
            stats_obj.start(file_suffix, self.stats_collect_details)
            fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format((int(iodepth) * int(num_jobs)), self.stats_collect_details))

            fio_job_name = "{}_{}_{}".format(self.fio_job_name, mode, iodepth * num_jobs)
            try:
                fio_output = end_host.pcie_fio(filename=nvme_block_device,
                                               rw=mode,
                                               numjobs=num_jobs,
                                               iodepth=iodepth,
                                               name=fio_job_name,
                                               **self.fio_cmd_args)
                fun_test.log("FIO Command Output:{}".format(fio_output))
                fun_test.test_assert(fio_output,
                                     "Fio {} test for numjobs {} & iodepth {}".format(mode, num_jobs, iodepth))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output:\n {}".format(fio_output))
            finally:
                # Stopping stats collection
                stats_obj.stop(self.stats_collect_details)
                self.storage_controller.verbose = True

            for index, value in enumerate(self.stats_collect_details):
                for func, arg in value.iteritems():
                    filename = arg.get("output_file")
                    if filename:
                        if func == "vp_utils":
                            fun_test.add_auxillary_file(description="F1 VP Utilization - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "per_vp":
                            fun_test.add_auxillary_file(description="F1 Per VP Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "resource_bam_args":
                            fun_test.add_auxillary_file(description="F1 Resource bam stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "vol_stats":
                            fun_test.add_auxillary_file(description="Volume Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "vppkts_stats":
                            fun_test.add_auxillary_file(description="VP Pkts Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "psw_stats":
                            fun_test.add_auxillary_file(description="PSW Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "fcp_stats":
                            fun_test.add_auxillary_file(description="FCP Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "wro_stats":
                            fun_test.add_auxillary_file(description="WRO Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "erp_stats":
                            fun_test.add_auxillary_file(description="ERP Stats - {} IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "etp_stats":
                            fun_test.add_auxillary_file(description="ETP Stats - {} IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "eqm_stats":
                            fun_test.add_auxillary_file(description="EQM Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "hu_stats":
                            fun_test.add_auxillary_file(description="HU Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "ddr_stats":
                            fun_test.add_auxillary_file(description="DDR Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "ca_stats":
                            fun_test.add_auxillary_file(description="CA Stats - {} IO depth {}".
                                                        format(mode, iodepth), filename=filename)
                        if func == "cdu_stats":
                            fun_test.add_auxillary_file(description="CDU Stats - {} - IO depth {}".
                                                        format(mode, iodepth), filename=filename)

    def cleanup(self):
        pass


class BltTcpSeqRead(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test sequential read queries on BLT volume over nvme fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Seq Read test(without verify) from the end host.''')


class BltTcpRandRead(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test random read queries on BLT volume over nvme fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Rand Read test(without verify) from the end host.''')


class BltTcpSeqRWMix(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Sequential read-write mix 70:30 ratio queries on BLT volume over nvme-tcp"
                                      " fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO mix seq read-write 70:30 test(without verify) from the end host.''')


class BltTcpSeqWRMix(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test Sequential write-read mix 70:30 ratio queries on BLT volume over nvme-tcp "
                                      "fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Seq write-read 70:30 test(without verify) from the end host.''')


class BltTcpRandRWMix(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test Random read-write mix 70:30 ratio queries on BLT volume over nvme-tcp "
                                      "fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO rand read-write 70:30 test(without verify) from the end host.''')


class BltTcpRandWRMix(BltTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test Random write-read mix 70:30 ratio queries on BLT volume over nvme-tcp "
                                      "fabric",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the network interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO random write-read 70:30 test(without verify) from the end host.''')


if __name__ == "__main__":
    bltscript = BLTVolumeSanityScript()
    # bltscript.add_test_case(BltTcpSeqRead())
    # bltscript.add_test_case(BltTcpRandRead())
    #bltscript.add_test_case(BltTcpSeqRWMix())
    # bltscript.add_test_case(BltTcpSeqWRMix())
    bltscript.add_test_case(BltTcpRandRWMix())
    # bltscript.add_test_case(BltTcpRandWRMix())

    bltscript.run()
