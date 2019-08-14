from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.fun.fs import Fs
from storage_helper import *
import fun_global


class ECVolumeLevelScript(FunTestScript):
    end_host = None
    storage_controller = None

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Setup COMe, launch DPC cli
        3. Configure Network interface between F1 and remote host.
        4. Create 4:2 EC volume and attach it to remote host.
        5. Execute write traffic to populate the EC volume.
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
        if not hasattr(self, "num_ssd"):
            self.num_ssd = 6
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        fs = topology.get_dut_instance(index=0)
        end_host = fs.get_come()
        storage_controller = StorageController(target_ip=end_host.host_ip,
                                               target_port=end_host.get_dpc_port(self.f1_in_use))
        if not check_come_health(storage_controller):
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology re-deployed")
            end_host = topology.get_dut_instance(index=0).get_come()
            storage_controller = StorageController(target_ip=end_host.host_ip,
                                                   target_port=end_host.get_dpc_port(self.f1_in_use))

        fun_test.shared_variables["end_host"] = end_host
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["storage_controller"] = storage_controller
        fun_test.shared_variables["setup_created"] = False
        fun_test.shared_variables['nsid'] = 0
        fun_test.shared_variables['db_log_time'] = get_current_time()
        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volumes"] = self.num_volume

        self.end_host = end_host
        self.storage_controller = storage_controller

        # create controller
        ctrlr_uuid = utils.generate_uuid()
        fun_test.test_assert(self.storage_controller.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                                       transport=self.transport,
                                                                       huid=self.huid,
                                                                       ctlid=self.ctlid,
                                                                       fnid=self.fnid,
                                                                       command_duration=self.command_timeout)['status'],
                             message="Create Controller with UUID: {}".format(ctrlr_uuid))
        fun_test.shared_variables["ctrlr_uuid"] = ctrlr_uuid

        # create ec_vol
        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)
        fun_test.test_assert(ec_config_status, message="Configure EC volume on F1")
        ec_uuid = self.ec_info["attach_uuid"][0]
        fun_test.test_assert(self.storage_controller.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=ec_uuid),
                             message="Attaching EC Vol nsid: {} with uuid {} to controller".format(self.ns_id, ec_uuid))
        fun_test.shared_variables['ec_uuid'] = ec_uuid

        # fetch nvme device
        fetch_nvme = fetch_nvme_device(end_host, self.ns_id)
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
        fun_test.shared_variables['nvme_block_device'] = fetch_nvme['nvme_device']
        fun_test.shared_variables['volume_name'] = fetch_nvme['volume_name']
        fun_test.shared_variables['ec_info'] = self.ec_info

        # set syslog level
        set_syslog_level(storage_controller, self.syslog_level)

        # Populate volume
        if self.warm_up_traffic:
            fio_output = self.end_host.pcie_fio(filename=fun_test.shared_variables['nvme_block_device'],
                                                **self.warm_up_fio_cmd_args)
            fun_test.test_assert(fio_output, "Pre-populating the volume")
        fun_test.shared_variables["setup_created"] = True

    def cleanup(self):
        try:
            if fun_test.shared_variables["setup_created"]:
                ctrlr_uuid = fun_test.shared_variables['ctrlr_uuid']
                # Detaching all the EC/LS volumes to the external server
                fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=ctrlr_uuid,
                    ns_id=self.ns_id,
                    command_duration=self.command_timeout)['status'],
                                     message="Detach nsid: {} from controller: {}".format(self.ns_id, ctrlr_uuid))

                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(ctrlr_uuid))

                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)
        except Exception as ex:
            fun_test.critical(str(ex))

        self.storage_controller.disconnect()
        fun_test.sleep("Allowing buffer time before clean-up", 5)
        fun_test.shared_variables["topology"].cleanup()


class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Num jobs and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_njobs_iodepth))
        # End of benchmarking json file parsing

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]
        storage_controller = fun_test.shared_variables["storage_controller"]
        end_host = fun_test.shared_variables["end_host"]

        fun_test.test_assert(fun_test.shared_variables['setup_created'], message="Check Setup got created successfully",
                             ignore_on_success=True)
        nvme_device = fun_test.shared_variables['nvme_block_device']
        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}

        table_data_rows = []
        job_inputs = fun_test.get_job_inputs()
        collect_artifacts = job_inputs[
            "collect_artifacts"] if job_inputs and "collect_artifacts" in job_inputs else True
        poll_interval = job_inputs["poll_interval"] if job_inputs and "poll_interval" in job_inputs else 30
        ec_details = get_ec_vol_uuids(ec_info=fun_test.shared_variables['ec_info'])

        for combo in self.fio_njobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}

            for mode in self.fio_modes:
                num_jobs, io_depth = eval(combo)
                fio_cmd_args = self.fio_cmd_args
                fio_cmd_args['numjobs'] = num_jobs
                fio_cmd_args['iodepth'] = io_depth
                fio_cmd_args['rw'] = mode
                fio_job_name = "ec_{0}_iodepth_{1}".format(mode, (num_jobs * io_depth))
                fio_cmd_args['name'] = fio_job_name

                fio_result[combo][mode] = True
                row_data_dict = {"mode": mode,
                                 "block_size": fio_cmd_args['bs'],
                                 "iodepth": io_depth * num_jobs,
                                 "size": fio_cmd_args["size"],
                                 "fio_job_name": fio_job_name}
                stats_collector = CollectStats(storage_controller)  # required to poll vol stats
                # initiate stats collection
                if collect_artifacts:
                    count = (fio_cmd_args['runtime'] + poll_interval) / poll_interval
                    vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(
                        post_fix_name="{}_vputil_artifact.txt".format(fio_job_name))
                    vol_stats_artifact_file = fun_test.get_test_case_artifact_file_name(
                        post_fix_name="{}_volstats_artifact.txt".format(fio_job_name))
                    thread_info = initiate_stats_collection(storage_controller=storage_controller,
                                                            interval=poll_interval,
                                                            count=count,
                                                            vp_util_artifact_file=vp_util_artifact_file,
                                                            vol_stats_artifact_file=vol_stats_artifact_file,
                                                            vol_details=ec_details)
                    active_threads = [thread_info['vp_util_thread_id'],thread_info['vol_stats_thread_id']]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".format(
                    mode, fio_cmd_args['bs'], io_depth * num_jobs))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = end_host.pcie_fio(filename=nvme_device, **fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                if collect_artifacts:
                    terminate_stats_collection(stats_ollector_obj=stats_collector, thread_list=active_threads)
                    fun_test.add_auxillary_file(description="F1 VP Utilization - {0} IO depth {1}".format(
                        mode, io_depth * num_jobs),
                        filename=vp_util_artifact_file)
                    fun_test.add_auxillary_file(description="F1 Volume Stats - {0} IO depth {1}".format(
                        mode, io_depth * num_jobs),
                        filename=vol_stats_artifact_file)
                fun_test.test_assert(fio_output[combo][mode], "Execute fio {0} only test with the block size:{1},"
                                                              "io_depth: {2}, num_jobs: {3}".
                                     format(mode, fio_cmd_args['bs'], fio_cmd_args['iodepth'], num_jobs))
                if mode == 'read' or mode == 'randread':  # default fio output write values to -1 before updating into db
                    for key in fio_output[combo][mode]['write']:
                        fio_output[combo][mode]['write'][key] = -1

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

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Building the table raw for this variation
                row_data_list = []
                for i in fio_perf_table_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                if fun_global.is_production_mode():
                    post_results("EC Volume",
                                 test_method,
                                 fun_test.shared_variables['db_log_time'],
                                 fun_test.shared_variables['num_ssd'],
                                 fun_test.shared_variables['num_volumes'],
                                 *row_data_list)

        table_data = {"headers": fio_perf_table_header, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for combo in self.fio_njobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class EC42FioSeqRandRead(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential and Random Read performance of EC volume over PCIE Interface.",
                              steps=""" 
        1. Run the FIO sequential and random read test(without verify) for required block size and IO depth from the 
        EP host.
        """)

    def setup(self):
        super(EC42FioSeqRandRead, self).setup()

    def run(self):
        super(EC42FioSeqRandRead, self).run()

    def cleanup(self):
        super(EC42FioSeqRandRead, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42FioSeqRandRead())
    ecscript.run()
