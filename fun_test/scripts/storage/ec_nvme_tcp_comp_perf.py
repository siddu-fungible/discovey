from lib.system.fun_test import *
from lib.fun.fs import Fs
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from storage_helper import *
from lib.host.linux import Linux
import fun_global
import copy

'''
Script to track the Storage Performance different reads for Compression enabled Erasure Coded volume using FIO.
'''


class ECVolumeLevelScript(FunTestScript):
    end_host = None
    storage_controller = None

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        config_file = fun_test.get_script_name_without_ext() + ".json"
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

        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if job_inputs and "boot_args" in job_inputs:
            self.bootargs = job_inputs["boot_args"]
        fun_test.shared_variables["post_result"] = job_inputs[
            "post_result"] if job_inputs and "post_result" in job_inputs else True
        host_spec = fun_test.get_asset_manager().get_host_spec(name=self.end_host_name)
        self.end_host = Linux(**host_spec)
        self.end_host.reboot(non_blocking=True)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0,
                                           custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "FS topology deployed")

        fs = topology.get_dut_instance(index=self.f1_in_use)
        come = fs.get_come()
        self.storage_controller = StorageController(target_ip=come.host_ip,
                                                    target_port=come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_inteface_index = None
        test_interface_name = None
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                if testbed_type == "fs-6" and host_ip != "poc-server-01":
                    continue
                self.end_host = host_info["host_obj"]
                test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(fpg_inteface_index))
                break
        else:
            fun_test.test_assert(False, "Host found with Test Interface")

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 6
        if not hasattr(self, "num_volume"):
            self.num_volume = 1
        # Configuring Linux host
        fun_test.test_assert(self.end_host.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                             message="End Host {} is up".format(self.end_host.host_ip))

        test_network = self.csr_network[str(fpg_inteface_index)]
        remote_ip = test_network["test_interface_ip"].split("/")[0]

        fun_test.shared_variables["test_network"] = test_network
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volumes"] = self.num_volume
        fun_test.shared_variables["numa_cpus"] = fetch_numa_cpus(self.end_host, self.ethernet_adapter)
        fun_test.shared_variables["db_log_time"] = get_current_time()
        fun_test.shared_variables["remote_ip"] = remote_ip

        configure_endhost_interface(end_host=self.end_host,
                                    test_network=test_network,
                                    interface_name=test_interface_name)

        # Loading the nvme and nvme_tcp modules
        load_nvme_module(self.end_host)
        load_nvme_tcp_module(self.end_host)

        # configure ip on FS
        fun_test.test_assert(self.storage_controller.ip_cfg(ip=test_network["f1_loopback_ip"])["status"],
                             "Configure IP {} on FS".format(test_network["f1_loopback_ip"]))

        # create controller
        ctlr_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_controller(ctrlr_id=0,
                                                                       ctrlr_uuid=ctlr_uuid,
                                                                       ctrlr_type="BLOCK",
                                                                       transport=self.attach_transport,
                                                                       remote_ip=remote_ip,
                                                                       subsys_nqn=self.nvme_subsystem,
                                                                       host_nqn=remote_ip,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)["status"],
                             "Create Storage Controller for {} with controller uuid {} on DUT".
                             format(self.attach_transport, ctlr_uuid))
        fun_test.shared_variables["ctlr_uuid"] = ctlr_uuid

    def cleanup(self):
        try:
            self.storage_controller.delete_controller(ctrlr_uuid=fun_test.shared_variables["ctlr_uuid"],
                                                      command_duration=self.command_timeout)
            self.storage_controller.disconnect()
        except Exception as ex:
            fun_test.critical(str(ex))
        fun_test.sleep(message="wait for logs to get flushed", seconds=45)
        fun_test.shared_variables["topology"].cleanup()


class ECVolumeLevelTestcase(FunTestCase):
    end_host = None
    storage_controller = None

    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # End of benchmarking json file parsing
        self.end_host = fun_test.shared_variables["end_host"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.numa_cpus = fun_test.shared_variables["numa_cpus"]
        ctlr_uuid = fun_test.shared_variables["ctlr_uuid"]
        test_network = fun_test.shared_variables["test_network"]
        self.remote_ip = fun_test.shared_variables['remote_ip']

        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)
        fun_test.test_assert(ec_config_status, "Configuring EC/LSV volume")

        fun_test.log("EC details after configuring EC Volume:")
        for k, v in self.ec_info.items():
            fun_test.log("{}: {}".format(k, v))

        # attach nvme device to controller
        fun_test.test_assert(self.storage_controller.attach_volume_to_controller(
            ns_id=self.ns_id,
            ctrlr_uuid=ctlr_uuid,
            vol_uuid=self.ec_info["attach_uuid"][0],
            command_duration=self.command_timeout)["status"],
                             message="Attach EC/LS volume on DUT with ns_id: {}".format(self.ns_id))

        # disabling the error_injection for the EC volume
        disable_error_inject(self.storage_controller)

        # Setting the syslog level
        set_syslog_level(storage_controller=self.storage_controller, log_level=self.syslog_level)

        # Checking nvme-connect status
        if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}".format(self.attach_transport.lower(),
                                                                             test_network["f1_loopback_ip"],
                                                                             self.transport_port,
                                                                             self.nvme_subsystem,
                                                                             self.remote_ip)
        else:
            nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                self.attach_transport.lower(),
                test_network["f1_loopback_ip"],
                self.transport_port,
                self.nvme_subsystem,
                self.io_queues,
                self.remote_ip)

        nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # Checking that the above created BLT volume is visible to the end host
        fetch_nvme = fetch_nvme_device(self.end_host, self.ns_id)
        fun_test.test_assert(fetch_nvme["status"], message="Check nvme device visible on end host")
        self.volume_name = fetch_nvme["volume_name"]
        self.nvme_block_device = fetch_nvme["nvme_device"]

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[4:]
        fun_test.simple_assert(self.nvme_block_device, message="Nvme block device fetched")
        warm_up_fio_cmd_args = self.warm_up_fio_cmd_args
        job_inputs = fun_test.get_job_inputs()
        collect_artifacts = job_inputs["collect_artifacts"] if job_inputs and "collect_artifacts" in job_inputs else True
        poll_interval = job_inputs["poll_interval"] if job_inputs and "poll_interval" in job_inputs else 30
        ec_details = get_ec_vol_uuids(ec_info=self.ec_info)
        stats_collector = CollectStats(self.storage_controller)  # required to poll vol stats

        for param in self.test_parameters:
            warm_up_fio_cmd_args["buffer_compress_percentage"] = param["compress_percent"]
            fun_test.test_assert(self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                        **warm_up_fio_cmd_args),
                                 message="Pre Populate Disk with {}% compressible Data".format(
                                     param["compress_percent"]))
            fio_result = {}
            fio_output = {}
            table_data_rows = []
            for combo in self.fio_numjobs_iodepth:
                fio_num_jobs, fio_iodepth = eval(combo)
                fio_result[combo] = {}
                fio_output[combo] = {}

                for mode in self.fio_modes:
                    fio_cmd_args = copy.copy(self.fio_cmd_args)
                    fio_cmd_args["rw"] = mode
                    fio_cmd_args["numjobs"] = fio_num_jobs
                    fio_cmd_args["iodepth"] = fio_iodepth
                    fio_cmd_args["cpus_allowed"] = self.numa_cpus
                    fio_cmd_args["name"] = "{}_{}_{}pctcomp_{}".format(self.fio_job_name,
                                                                       mode,
                                                                       param["compress_percent"],
                                                                       (fio_num_jobs * fio_iodepth))
                    if mode == "write":
                        fio_cmd_args["buffer_pattern"] = warm_up_fio_cmd_args["buffer_pattern"]
                        fio_cmd_args["buffer_compress_percentage"] = param['compress_percent']
                    if collect_artifacts:
                        count = (fio_cmd_args["runtime"] + poll_interval) / poll_interval
                        vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_vputil_artifact.txt".format(fio_cmd_args["name"]))
                        vol_stats_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_vol_stats_artifact.txt".format(fio_cmd_args["name"]))
                        bam_stats_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_bam_stats_artifact.txt".format(fio_cmd_args["name"]))
                        thread_info = initiate_stats_collection(storage_controller=self.storage_controller,
                                                                interval=poll_interval,
                                                                count=count,
                                                                vp_util_artifact_file=vp_util_artifact_file,
                                                                vol_stats_artifact_file=vol_stats_artifact_file,
                                                                bam_stats_articat_file=bam_stats_artifact_file,
                                                                vol_details=ec_details)
                        active_threads = [thread_info['vp_util_thread_id'], thread_info['vol_stats_thread_id'], thread_info["bam_stats_thread_id"]]

                    fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                                     **fio_cmd_args)
                    if collect_artifacts:
                        terminate_stats_collection(stats_ollector_obj=stats_collector, thread_list=active_threads)
                        fun_test.add_auxillary_file(description="F1 VP Utilization - {0} IO depth {1}".format(
                            mode, fio_cmd_args["iodepth"] * fio_cmd_args["numjobs"]),
                            filename=vp_util_artifact_file)
                        fun_test.add_auxillary_file(description="F1 Volume Stats - {0} IO depth {1}".format(
                            mode, fio_cmd_args["iodepth"] * fio_cmd_args["numjobs"]),
                            filename=vol_stats_artifact_file)
                        fun_test.add_auxillary_file(description="F1 Bam Resource Stats - {0} IO depth {1}".format(
                            mode, fio_cmd_args["iodepth"] * fio_cmd_args["numjobs"]),
                            filename=bam_stats_artifact_file)

                    fun_test.test_assert(fio_output[combo][mode],
                                         message="Execute fio with mode:{0}, iodepth: {1}, num_jobs: {2} "
                                                 "and cpus: {3}".format(mode, fio_iodepth, fio_num_jobs,
                                                                        self.numa_cpus))
                    fio_result[combo][mode] = True

                    row_data_dict = {"mode": mode,
                                     "block_size": fio_cmd_args["bs"],
                                     "iodepth": fio_iodepth * fio_num_jobs,
                                     "size": "{}G".format(self.ec_info["capacity"] >> 30),
                                     "fio_job_name": fio_cmd_args["name"]}

                    if mode == "read" or mode == "randread":
                        for key in fio_output[combo][mode]["write"]:
                            fio_output[combo][mode]["write"][key] = -1
                    elif mode == "write":
                        for key in fio_output[combo][mode]["read"]:
                            fio_output[combo][mode]["read"][key] = -1

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

                    row_data_list = []
                    for i in fio_perf_table_cols:
                        if i not in row_data_dict:
                            row_data_list.append(-1)
                        else:
                            row_data_list.append(row_data_dict[i])

                    table_data_rows.append(row_data_list)
                    if fun_global.is_production_mode() and fun_test.shared_variables["post_result"]:
                        post_results(testcase,
                                     test_method,
                                     fun_test.shared_variables["db_log_time"],
                                     fun_test.shared_variables["num_ssd"],
                                     fun_test.shared_variables["num_volumes"],
                                     *row_data_list)

            table_data = {"headers": fio_perf_table_header, "rows": table_data_rows}
            fun_test.add_table(panel_header=self.summary,
                               table_name=param["name"],
                               table_data=table_data)

    def cleanup(self):
        try:
            # disconnect volume from controller
            ctlr_uuid = fun_test.shared_variables["ctlr_uuid"]
            fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                ctrlr_uuid=ctlr_uuid,
                ns_id=self.ns_id,
                command_duration=self.command_timeout)["status"],
                                 message="Detach nsid: {} from controller: {}".format(self.ns_id, ctlr_uuid))
            fun_test.test_assert(self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                                               command_timeout=self.command_timeout),
                                 message="Unconfigure EC Volume from SSD")
        except Exception as ex:
            fun_test.critical(ex.message)


class EC42NvmeTcpCompPerf(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="EC volume performance for sequential and random read queries with 1%, 50% and "
                                      "80% compressible data, over NVME/TCP.",
                              steps="""
        1. Create 6 BLT volumes on dut instance.
        2. Create a 4:2 EC volume on top of the 6 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to the EP host connected via the NVME/TCP interface. 
        5. Run the FIO sequential read only test(without verify) for required block size and IO depth from the 
        EP host for 1% compressible data, 50% compressible data and 80% compressible data.
        6. Repeat step 5 for random read queries and log the result.
        """)

    def setup(self):
        super(EC42NvmeTcpCompPerf, self).setup()

    def run(self):
        super(EC42NvmeTcpCompPerf, self).run()

    def cleanup(self):
        super(EC42NvmeTcpCompPerf, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42NvmeTcpCompPerf())
    ecscript.run()
