from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
import fun_global
from lib.fun.fs import Fs
from lib.system import utils
from datetime import datetime
from ec_perf_helper import *


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
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

        self.end_host = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip,
                                                    target_port=self.come.get_dpc_port(self.f1_in_use))

        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", 2], legacy=False,
                                                      command_duration=5)
        fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=2, actual=command_result["data"], message="Checking syslog level")

        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        try:
            self.ec_info = fun_test.shared_variables["ec_info"]
            self.remote_ip = fun_test.shared_variables["remote_ip"]
            self.attach_transport = fun_test.shared_variables["attach_transport"]

            if fun_test.shared_variables["ec"]["setup_created"]:
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.volume_detach_remote(ns_id=num + 1,
                                                                                  uuid=self.ec_info["attach_uuid"][num],
                                                                                  huid=self.huid,
                                                                                  ctlid=self.ctlid,
                                                                                  transport=self.attach_transport,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)
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

        # fio_bs_iodepth variable is a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size
        # Checking the block size and IO depth combo list availability
        if 'fio_njobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_njobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Checking the availability of expected FIO results
        # Checking the availability of expected volume level internal stats at the end of every FIO run
        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting FIO passing threshold percentage to {} for this {} testcase, because its not set in "
                         "the {} file".format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Num jobs and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_njobs_iodepth))
        # End of benchmarking json file parsing

        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volume"] = self.num_volume

        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.end_host = fun_test.shared_variables["end_host"]

        fun_test.shared_variables["ec_coding"] = self.ec_coding
        self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])
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
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            # Attaching/Exporting all the EC/LS volumes to the external server
            fun_test.shared_variables["ec"]["setup_created"] = True

            # disabling the error_injection for the EC volume
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                          command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),  # Todo Check if int() is req
                                          expected=0,
                                          message="Ensuring error_injection got disabled")

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level",
                                                          legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level,
                                          actual=command_result["data"],
                                          message="Checking syslog level")

            # Attaching/Exporting the EC/LS volume to the external server
            fun_test.test_assert(self.storage_controller.volume_attach_pcie(ns_id=self.ns_id,
                                                                            uuid=self.ec_info["attach_uuid"][0],
                                                                            huid=self.huid,
                                                                            ctlid=self.ctlid,
                                                                            command_duration=self.command_timeout)[
                                     "status"], "Attaching EC/LS volume on DUT")

            # disabling the error_injection for the EC volume

            fun_test.test_assert(self.storage_controller.poke(props_tree=["params/ecvol/error_inject", 0],
                                                              legacy=False,
                                                              command_duration=self.command_timeout)["status"],
                                 "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)

            fun_test.test_assert(self.storage_controller.peek(props_tree="params/ecvol", legacy=False,
                                                              command_duration=self.command_timeout)["status"],
                                 "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),
                                          expected=0,
                                          message="Ensuring error_injection got disabled")

            # fun_test.shared_variables[self.ec_ratio]["storage_controller"] = self.storage_controller
            fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids

            lsblk_output = self.end_host.lsblk("-b")
            fun_test.simple_assert(lsblk_output, "Listing available volumes")

            # Checking that the above created BLT volume is visible to the end host # TOdo move to helper
            fetch_response = fetch_nvme_device(end_host=self.end_host, nsid=self.ns_id)
            fun_test.test_assert(fetch_response['status'], message="Check nvme device is visible")
            self.nvme_block_device = fetch_response['nvme_device']

            fun_test.shared_variables[self.ec_ratio]["setup_created"] = True
            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device

            # Disable the udev daemon which will skew the read stats of the volume during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for service in udev_services:
                service_status = self.end_host.systemctl(service_name=service, action="stop")
                fun_test.test_assert(service_status, "Stopping {} service".format(service))

            # Executing the FIO command to warm up the system
            if self.warm_up_traffic:
                fun_test.log("Executing the FIO command to warm up the system")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        if self.ec_ratio in fun_test.shared_variables or fun_test.shared_variables[self.ec_ratio]["setup_created"]:
            self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

        # self.storage_controller = fun_test.shared_variables[self.ec_ratio]["storage_controller"]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}

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
                fun_test.test_assert(command_result["status"], "Inject failure to the BLT volume having the UUID "
                                                               "{}".format(self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              command_duration=self.command_timeout)
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
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_cmd_args['bs']
                row_data_dict["iodepth"] = io_depth
                row_data_dict["size"] = fio_cmd_args["size"]
                row_data_dict["fio_job_name"] = fio_job_name

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_cmd_args['bs'], io_depth, self.ec_ratio))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,  **self.fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                fun_test.test_assert(fio_output[combo][mode], "Execute fio {0} only test with the block size:{1},"
                                                              "io_depth: {2}, num_jobs: {3}".
                                     format(mode, fio_cmd_args['bs'], fio_cmd_args['iodepth'], num_jobs))

                # Boosting the fio output with the testbed performance multiplier
                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                if fun_global.is_production_mode():
                    post_results("EC Volume", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
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
                fun_test.test_assert(command_result["status"], "Disable failure from the {} volume having the UUID "
                                                               "{}".format(vtype, self.uuids[vtype][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", vtype, self.uuids[vtype][index], "stats")
                command_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              command_duration=self.command_timeout)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]),
                                              expected=0,
                                              message="Ensuring fault_injection got disabled")


class EC42FioSeqReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read only performance of EC volume",
                              steps="""
        1. Create 6 BLT volumes on dut instance.
        2. Create a 4:2 EC volume on top of the 6 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to the EP host connected via the PCIe interface. 
        5. Run the FIO sequential read only test(without verify) for required block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC42FioSeqReadOnly, self).setup()

    def run(self):
        super(EC42FioSeqReadOnly, self).run()

    def cleanup(self):
        super(EC42FioSeqReadOnly, self).cleanup()


class EC42FioRandReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read only performance of EC volume",
                              steps="""
        1. Create 6 BLT volumes in dut instance.
        2. Create a 4:2 EC volume on top of the 6 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to the EP host connected via the PCIe interface.
        5. Run the FIO random read only test(without verify) for required block size and IO depth from the 
        EP host and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC42FioRandReadOnly, self).setup()

    def run(self):
        super(EC42FioRandReadOnly, self).run()

    def cleanup(self):
        super(EC42FioRandReadOnly, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42FioSeqReadOnly())
    ecscript.add_test_case(EC42FioRandReadOnly())
    ecscript.run()
