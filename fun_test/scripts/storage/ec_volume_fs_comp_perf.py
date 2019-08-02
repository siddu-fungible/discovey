from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.fun.fs import Fs
from storage_helper import *
import fun_global

VOL_TYPE = "EC_COMP_FS_VOL"


def parse_perf_stats(perf_dict):
    for k in perf_dict:
        if k == "iops" or k == "latency":
            perf_dict[k] = int(round(perf_dict[k]))
        if k == "bw":
            perf_dict[k] = int(round(perf_dict[k] / 1000))
    return perf_dict


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
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        fun_test.shared_variables["post_result"] = job_inputs[
            "post_result"] if job_inputs and "post_result" in job_inputs else True

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0,
                                           custom_boot_args=self.bootargs,
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
        fun_test.shared_variables["storage_controller"] = storage_controller
        fun_test.shared_variables['nsid'] = 0
        fun_test.shared_variables['db_log_time'] = get_current_time()
        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volume"] = self.num_volume

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

    def cleanup(self):
        try:
            ctrlr_uuid = fun_test.shared_variables['ctrlr_uuid']
            # Detaching all the EC/LS volumes to the external server

            fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                           command_duration=self.command_timeout),
                                 message="Delete Controller uuid: {}".format(ctrlr_uuid))
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
        self.end_host = fun_test.shared_variables["end_host"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
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

        # create ec_vol
        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)
        fun_test.test_assert(ec_config_status, message="Configure EC volume on F1")
        ec_uuid = self.ec_info["attach_uuid"][0]
        ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
        fun_test.test_assert(self.storage_controller.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=ec_uuid),
                             message="Attaching EC Vol nsid: {} with uuid {} to controller".format(self.ns_id, ec_uuid))

        # fetch nvme device
        fetch_nvme = fetch_nvme_device(end_host=self.end_host, nsid=self.ns_id)
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
        self.nvme_device = fetch_nvme['nvme_device']

        # set syslog level
        set_syslog_level(self.storage_controller, self.syslog_level)

    def run(self):
        table_data_header = None
        testcase = self.__class__.__name__
        stats_table_lst = []
        job_perfix = self.read_fio_cmd_args['name']
        for test in self.test_parameters:

            set_header = True
            table_rows = []
            # Perform Writes With specified % of Compressible data
            self.write_fio_cmd_args['buffer_compress_percentage'] = test['compress_percent']
            fun_test.test_assert(self.end_host.pcie_fio(filename=self.nvme_device, **self.write_fio_cmd_args),
                                 message="Execute {0} write on nvme device {1} compress percentage: {2}%".format(
                                     self.write_fio_cmd_args['size'],
                                     self.nvme_device,
                                     self.write_fio_cmd_args['buffer_compress_percentage']))
            # Do seq and rand read for the writes
            for mode in self.fio_modes:
                self.read_fio_cmd_args['rw'] = mode
                self.read_fio_cmd_args['name'] = "{0}_{1}_{2}".format(job_perfix,
                                                                      mode,
                                                                      self.write_fio_cmd_args[
                                                                          'buffer_compress_percentage'])
                fio_read_output = self.end_host.pcie_fio(filename=self.nvme_device, **self.read_fio_cmd_args)
                fun_test.test_assert(fio_read_output,
                                     message="Execute {0} {1} on nvme device {2} ".format(
                                         self.read_fio_cmd_args['size'],
                                         self.read_fio_cmd_args['rw'],
                                         self.nvme_device))
                perf_stats = parse_perf_stats(fio_read_output['read'])
                if set_header:
                    set_header = False
                    table_data_header = sorted(perf_stats.keys())
                table_row1 = [perf_stats[key] for key in table_data_header]
                perf_stats['block_size'] = self.read_fio_cmd_args['bs']
                perf_stats['iodepth'] = self.read_fio_cmd_args['iodepth']
                perf_stats['operation'] = self.read_fio_cmd_args['rw']
                perf_stats['job_name'] = self.read_fio_cmd_args['name']
                perf_stats['size'] = self.read_fio_cmd_args['size']

                if fun_global.is_production_mode() and fun_test.shared_variables["post_result"]:
                    fun_test.log("Updating the following stats on database: {}".format(perf_stats))
                    self.post_results(test=testcase, test_stats=perf_stats)  # publish only compression stats on db
                table_row1.insert(0, "<b>{}</b>".format(mode.capitalize()))
                table_rows.append(table_row1)
            table_data_header.insert(0, "")  # Align Table according to rows
            table_data = {"headers": table_data_header, "rows": table_rows}
            stats_table_lst.append({'table_name': test['name'], 'table_data': table_data})

        # Print Tabulated Stats
        panel_header = testcase + " Performance Stats"
        for stats in stats_table_lst:
            fun_test.add_table(panel_header=panel_header,
                               table_name=stats['table_name'], table_data=stats['table_data'])

    def post_results(self, test, test_stats):
        blt = BltVolumePerformanceHelper()

        blt.add_entry(date_time=fun_test.shared_variables['db_log_time'],
                      volume=VOL_TYPE,
                      test=test,
                      block_size=test_stats['block_size'],
                      io_depth=test_stats['iodepth'],
                      size=test_stats['size'],
                      operation=test_stats['operation'],
                      num_ssd=fun_test.shared_variables["num_ssd"],
                      num_volume=fun_test.shared_variables["num_volume"],
                      fio_job_name=test_stats['job_name'],
                      read_iops=test_stats['iops'],
                      read_throughput=test_stats['bw'],
                      read_avg_latency=test_stats['latency'],
                      read_90_latency=test_stats['latency90'],
                      read_95_latency=test_stats['latency95'],
                      read_99_latency=test_stats['latency99'],
                      read_99_99_latency=test_stats['latency9999'],
                      read_iops_unit="ops",
                      read_throughput_unit="MBps",
                      read_avg_latency_unit="usecs",
                      read_90_latency_unit="usecs",
                      read_95_latency_unit="usecs",
                      read_99_latency_unit="usecs",
                      read_99_99_latency_unit="usecs")

    def cleanup(self):
        # detach volume from controller
        ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
        fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
            ctrlr_uuid=ctrlr_uuid,
            ns_id=self.ns_id,
            command_duration=self.command_timeout)['status'],
                             message="Detach nsid: {} from controller: {}".format(self.ns_id, ctrlr_uuid))
        self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                      command_timeout=self.command_timeout)
        # delete volume


class EC42FioReadEffortAuto(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Sequential and Random reads for Compression enabled 4:2 EC volume"
                                      " Effort: Auto",
                              steps="""
                              1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                                 a Journal Volume and an LSV volume with compression enabled effort Auto.
                              2. Attach LSV volume to the nvme controller.  
                              3. Execute writes on NVME device.
                              4. Perform sequential read for above write, log performance stats.
                              5. Perform random read for above write, log performance stats.
                              6. Repeat step 1,2,3 for 50% and 80% compressible data. 
                              """)

    def setup(self):
        super(EC42FioReadEffortAuto, self).setup()

    def run(self):
        super(EC42FioReadEffortAuto, self).run()

    def cleanup(self):
        super(EC42FioReadEffortAuto, self).cleanup()


class EC42FioReadCompDisabled(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Sequential and Random reads for 4:2 EC volume with Compression Disabled",
                              steps="""
                              1. Create 6 BLT volumes, Configure 1 EC(4:2) on top of the BLT volume, 
                                 a Journal Volume and an LSV volume.
                              2. Attach LSV volume to the nvme controller.
                              1. Execute writes on NVME device with compressibility 1%.
                              2. Perform sequential read for above write, log performance stats.
                              3. Perform random read for above write, log performance stats.
                              4. Repeat step 1,2,3 for 50% and 80% compressible data. 
                              """)

    def setup(self):
        super(EC42FioReadCompDisabled, self).setup()

    def run(self):
        super(EC42FioReadCompDisabled, self).run()

    def cleanup(self):
        super(EC42FioReadCompDisabled, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42FioReadEffortAuto())
    ecscript.add_test_case(EC42FioReadCompDisabled())
    ecscript.run()
