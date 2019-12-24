from lib.system.fun_test import *
from lib.fun.fs import Fs
from datetime import datetime
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.system import utils
from storage_helper import *
import fun_global

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


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

        if "GlobalSetup" not in config_dict:
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

        testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0,
                                           custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        self.fs = topology.get_dut_instance(index=0)

        come = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=come.host_ip,
                                                    target_port=come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0,
                                                                            f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if testbed_type == "fs-6" and host_ip != "poc-server-01":
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
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables['db_log_time'] = get_current_time()

        # Fetching NUMA node from Network host for mentioned Ethernet Adapter card
        fun_test.shared_variables["numa_cpus"] = fetch_numa_cpus(self.end_host, self.ethernet_adapter)

        # Configuring Linux host
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
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Adding static ARP to F1 route")

        # Loading the nvme and nvme_tcp modules
        self.end_host.modprobe(module="nvme")
        fun_test.sleep("Loading nvme module", 2)

        fun_test.test_assert_expected(actual=self.end_host.lsmod(module="nvme")['name'],
                                      expected="nvme",
                                      message="Loading nvme module")

        self.end_host.modprobe(module="nvme_tcp")
        fun_test.sleep("Loading nvme_tcp module", 2)
        fun_test.test_assert_expected(expected="nvme_tcp", actual=self.end_host.lsmod(module="nvme_tcp")['name'],
                                      message="Loading nvme_tcp module")
        pass

    def cleanup(self):
        try:
            if fun_test.shared_variables["ec"]["setup_created"]:
                ec_info = fun_test.shared_variables["ec_info"]
                attach_ns_id = fun_test.shared_variables["ns_id"]
                ctrlr_uuid = fun_test.shared_variables['ctrlr_uuid']
                fun_test.test_assert(self.storage_controller.detach_volume_from_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                           ns_id=attach_ns_id,
                                                                                           command_duration=self.command_timeout)[
                                         'status'],
                                     message="Detach nsid: {} from controller: {}".format(attach_ns_id, ctrlr_uuid))

                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(ctrlr_uuid))

                self.storage_controller.unconfigure_ec_volume(ec_info=ec_info,
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
        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)
        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 6
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        self.end_host = fun_test.shared_variables["end_host"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.numa_cpus = fun_test.shared_variables["numa_cpus"]

        fun_test.shared_variables["num_ssd"] = self.num_ssd
        fun_test.shared_variables["num_volumes"] = self.num_ssd

        self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            # Configuring the controller
            # enable_counters(self.storage_controller, self.command_timeout)

            fun_test.test_assert(self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])["status"],
                                 "ip_cfg configured on DUT instance")
            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(ctrlr_id=0,
                                                                       ctrlr_uuid=self.ctrlr_uuid,
                                                                       ctrlr_type="BLOCK",
                                                                       transport=self.attach_transport,
                                                                       remote_ip=self.remote_ip,
                                                                       subsys_nqn=self.nvme_subsystem,
                                                                       host_nqn=self.remote_ip,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create Storage Controller for {} with controller uuid {} on DUT".
                                 format(self.attach_transport, self.ctrlr_uuid))
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=self.ec_info["attach_uuid"][
                                                                                     0],
                                                                                 command_duration=self.command_timeout)

            fun_test.test_assert(command_result["status"],
                                 "Attach EC/LS volume with nsid: {} to controller with uuid: {}".format(self.ns_id,
                                                                                                        self.ctrlr_uuid))
            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables['ns_id'] = self.ns_id
            # disabling the error_injection for the EC volume
            fun_test.test_assert(self.storage_controller.poke("params/ecvol/error_inject 0",
                                                              command_duration=self.command_timeout)["status"],
                                 "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"],
                                 "Retrieving error_injection status on DUT", ignore_on_success=True)
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),
                                          expected=0,
                                          message="Ensuring error_injection got disabled")

            # Setting the syslog level
            fun_test.test_assert(self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                              legacy=False,
                                                              command_duration=self.command_timeout)[
                                     "status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level",
                                                          legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

        if not fun_test.shared_variables["ec"]["nvme_connect"]:
            # Checking nvme-connect status
            if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                                 self.test_network["f1_loopback_ip"],
                                                                                 self.transport_port,
                                                                                 self.nvme_subsystem)
            else:
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                    self.attach_transport.lower(), self.test_network["f1_loopback_ip"], self.transport_port,
                    self.nvme_subsystem, self.io_queues)

            nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
            fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

            # Checking that the above created BLT volume is visible to the end host
            fetch_nvme = fetch_nvme_device(self.end_host, self.ns_id)
            fun_test.test_assert(fetch_nvme['status'], message="Check nvme device visible on end host")
            self.volume_name = fetch_nvme['volume_name']
            self.nvme_block_device = fetch_nvme['nvme_device']

            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["ec"]["nvme_connect"] = True

    def run(self):
        testcase = self.__class__.__name__

        self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
        self.volume_name = fun_test.shared_variables["volume_name"]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

        stats_table_lst = []
        job_inputs = fun_test.get_job_inputs()
        collect_artifacts = job_inputs[
            "collect_artifacts"] if job_inputs and "collect_artifacts" in job_inputs else True
        poll_interval = job_inputs["poll_interval"] if job_inputs and "poll_interval" in job_inputs else 30
        ec_details = get_ec_vol_uuids(ec_info=self.ec_info)
        stats_collector = CollectStats(self.storage_controller)  # required to poll vol stats
        for param in self.test_parameters:
            self.warm_up_fio_cmd_args['buffer_compress_percentage'] = param['compress_percent']
            fun_test.test_assert(self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                        cpus_allowed=self.numa_cpus,
                                                        **self.warm_up_fio_cmd_args),
                                 message="Pre Populate Disk with {}% compressible Data".format(
                                     param['compress_percent']))
            fio_result = {}
            fio_output = {}
            table_data_rows = []
            for combo in self.fio_numjobs_iodepth:
                fio_num_jobs, fio_iodepth = eval(combo)
                fio_result[combo] = {}
                fio_output[combo] = {}

                for mode in self.fio_modes:
                    fun_test.sleep("Wait between iterations", 2)
                    fio_job_name = "{}_{}_{}pctcomp_{}".format(self.fio_job_name, mode, param['compress_percent'],
                                                               (fio_num_jobs * fio_iodepth))
                    if collect_artifacts:
                        count = (self.fio_cmd_args["runtime"] + poll_interval) / poll_interval
                        vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_vputil_artifact.txt".format(fio_job_name))
                        vol_stats_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_vol_stats_artifact.txt".format(fio_job_name))
                        bam_stats_artifact_file = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}_bam_stats_artifact.txt".format(fio_job_name))
                        thread_info = initiate_stats_collection(storage_controller=self.storage_controller,
                                                                interval=poll_interval,
                                                                count=count,
                                                                vp_util_artifact_file=vp_util_artifact_file,
                                                                vol_stats_artifact_file=vol_stats_artifact_file,
                                                                bam_stats_articat_file=bam_stats_artifact_file,
                                                                vol_details=ec_details)
                    active_threads = [thread_info['vp_util_thread_id'], thread_info['vol_stats_thread_id'],
                                      thread_info['bam_stats_thread_id']]

                    fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                                     rw=mode,
                                                                     numjobs=fio_num_jobs,
                                                                     iodepth=fio_iodepth,
                                                                     name=fio_job_name,
                                                                     cpus_allowed=self.numa_cpus,
                                                                     **self.fio_cmd_args)
                    if collect_artifacts:
                        terminate_stats_collection(stats_ollector_obj=stats_collector, thread_list=active_threads)
                        fun_test.add_auxillary_file(description="F1 VP Utilization - {0} IO depth {1}".format(
                            mode, fio_num_jobs * fio_iodepth),
                            filename=vp_util_artifact_file)
                        fun_test.add_auxillary_file(description="F1 Volume Stats - {0} IO depth {1}".format(
                            mode, fio_num_jobs * fio_iodepth),
                            filename=vol_stats_artifact_file)
                        fun_test.add_auxillary_file(description="F1 Bam Stats - {0} IO depth {1}".format(
                            mode, fio_num_jobs * fio_iodepth),
                            filename=bam_stats_artifact_file)
                    fun_test.test_assert(fio_output[combo][mode],
                                         message="Execute fio with mode:{0}, iodepth: {1}, num_jobs: {2} "
                                                 "and cpus: {3}".format(mode, fio_iodepth, fio_num_jobs,
                                                                        self.numa_cpus))
                    fio_result[combo][mode] = True

                    row_data_dict = {'mode': mode,
                                     "block_size": self.fio_cmd_args["bs"],
                                     'iodepth': fio_iodepth * fio_num_jobs,
                                     'size': '{}'.format(self.ec_info["capacity"] >> 30),
                                     'fio_job_name': fio_job_name}

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
                    if fun_global.is_production_mode():
                        post_results("EC42_CompressionVol",
                                     testcase,
                                     fun_test.shared_variables['db_log_time'],
                                     fun_test.shared_variables['num_ssd'],
                                     fun_test.shared_variables['num_volumes'],
                                     *row_data_list)

            table_data = {"headers": fio_perf_table_header, "rows": table_data_rows}
            stats_table_lst.append({'table_name': param['name'], 'table_data': table_data})

        panel_header = testcase + " Performance Stats"
        for stat in stats_table_lst:
            fun_test.add_table(panel_header=panel_header, table_name=stat['table_name'], table_data=stat['table_data'])

    def cleanup(self):
        pass


class EC42RandReadWr8kEffortAuto(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.14.1: 8k data block random read/write IOPS performance of EC volume,"
                                      "Compression enabled, Effort: Auto, Algorithm: Deflate",
                              steps="""
                              1. Bring up F1 in FS1600
                              2. Bring up and configure Remote Host
                              3. Create 6 BLT volumes on dut instance.
                              4. Create a 4:2 EC volume on top of the 6 BLT volumes.
                              5. Create a LS volume on top of the EC volume based on use_lsv config along with its 
                              associative journal volume.
                              6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host
                              7. Run warm-up traffic using FIO with 1% compressible data.
                              8. Run the Performance for 8k transfer size Random read/write IOPS
                              9. Repeat step 7 & 8 for 50% compressible data and 80% compressible data.""")

    def setup(self):
        super(EC42RandReadWr8kEffortAuto, self).setup()

    def run(self):
        super(EC42RandReadWr8kEffortAuto, self).run()

    def cleanup(self):
        super(EC42RandReadWr8kEffortAuto, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC42RandReadWr8kEffortAuto())
    ecscript.run()
