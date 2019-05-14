from lib.system.fun_test import *
from lib.fun.fs import Fs
from datetime import datetime
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from ec_perf_helper import *
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

        # Fetching NUMA node from Network host for mentioned Ethernet Adapter card
        lspci_output = self.end_host.lspci(grep_filter=self.ethernet_adapter)
        fun_test.simple_assert(lspci_output, "Ethernet Adapter Detected")
        adapter_id = lspci_output[0]['id']
        fun_test.simple_assert(adapter_id, "Ethernet Adapter Bus ID Retrieved")
        lspci_verbose_output = self.end_host.lspci(slot=adapter_id, verbose=True)
        numa_node = lspci_verbose_output[0]['numa_node']
        fun_test.test_assert(numa_node, "Ethernet Adapter NUMA Node Retrieved")

        # Fetching NUMA CPUs for above fetched NUMA Node
        lscpu_output = self.end_host.lscpu(grep_filter="node{}".format(numa_node))
        fun_test.simple_assert(lscpu_output, "CPU associated to Ethernet Adapter NUMA")

        self.numa_cpus = lscpu_output.values()[0]
        fun_test.test_assert(self.numa_cpus, "CPU associated to Ethernet Adapter NUMA")
        fun_test.log("Ethernet Adapter: {}, NUMA Node: {}, NUMA CPU: {}".format(self.ethernet_adapter, numa_node,
                                                                                self.numa_cpus))

        fun_test.shared_variables["numa_cpus"] = self.numa_cpus

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
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Configuring test interface IP address")

        self.end_host.sudo_command(command=interface_mac_config,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Assigning MAC to test interface")

        self.end_host.sudo_command(command=link_up_cmd,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Bringing up test link")

        interface_up_status = self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                             action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                   gateway=self.test_network["test_net_route"]["gw"],
                                   outbound_interface=self.test_interface_name,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Adding route to F1")

        self.end_host.sudo_command(command=static_arp_cmd,
                                   timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0,
                                      actual=self.end_host.exit_status(),
                                      message="Adding static ARP to F1 route")

        # Loading the nvme and nvme_tcp modules
        self.end_host.modprobe(module="nvme")
        fun_test.sleep("Loading nvme module", 2)
        command_result = self.end_host.lsmod(module="nvme")
        fun_test.simple_assert(command_result, "Loading nvme module")
        fun_test.test_assert_expected(expected="nvme",
                                      actual=command_result['name'],
                                      message="Loading nvme module")

        self.end_host.modprobe(module="nvme_tcp")
        fun_test.sleep("Loading nvme_tcp module", 2)
        command_result = self.end_host.lsmod(module="nvme_tcp")
        fun_test.simple_assert(command_result, "Loading nvme_tcp module")
        fun_test.test_assert_expected(expected="nvme_tcp",
                                      actual=command_result['name'],
                                      message="Loading nvme_tcp module")

    def cleanup(self):

        self.ec_info = fun_test.shared_variables["ec_info"]
        self.remote_ip = fun_test.shared_variables["remote_ip"]
        self.attach_transport = fun_test.shared_variables["attach_transport"]

        try:
            if fun_test.shared_variables["ec"]["setup_created"]:
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.volume_detach_remote(ns_id=num + 1,
                                                                                  uuid=self.ec_info["attach_uuid"][num],
                                                                                  huid=self.huid, ctlid=self.ctlid,
                                                                                  remote_ip=self.remote_ip,
                                                                                  transport=self.attach_transport,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                unconfigure_ec_volume(storage_controller=self.storage_controller,
                                      ec_info=self.ec_info,
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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        # End of benchmarking json file parsing

        self.fs = fun_test.shared_variables["fs"]
        self.end_host = fun_test.shared_variables["end_host"]
        self.test_network = fun_test.shared_variables["test_network"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.numa_cpus = fun_test.shared_variables["numa_cpus"]

        fun_test.shared_variables["attach_transport"] = self.attach_transport
        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd

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
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

            (ec_config_status, self.ec_info) = configure_ec_volume(self.storage_controller, self.ec_info,
                                                                   self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            # Attaching/Exporting all the EC/LS volumes to the external server
            self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
            fun_test.shared_variables["remote_ip"] = self.remote_ip

            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.volume_attach_remote(ns_id=num + 1,
                                                                              uuid=self.ec_info["attach_uuid"][num],
                                                                              huid=self.huid, ctlid=self.ctlid,
                                                                              remote_ip=self.remote_ip,
                                                                              transport=self.attach_transport,
                                                                              command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Attach {} EC/LS volume on DUT".format(num))

            fun_test.shared_variables["ec"]["setup_created"] = True

            # disabling the error_injection for the EC volume
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                          command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),
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

        if not fun_test.shared_variables["ec"]["nvme_connect"]:
            # Checking nvme-connect status
            if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                                 self.test_network["f1_loopback_ip"],
                                                                                 str(self.transport_port),
                                                                                 self.nvme_subsystem)
            else:
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                    self.attach_transport.lower(), self.test_network["f1_loopback_ip"], str(self.transport_port),
                    self.nvme_subsystem, str(self.io_queues))

            nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
            fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

            lsblk_output = self.end_host.lsblk("-b")
            fun_test.simple_assert(lsblk_output, "Listing available volumes")

            # Checking that the above created BLT volume is visible to the end host
            volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(self.ns_id)
            for volume_name in lsblk_output:
                match = re.search(volume_pattern, volume_name)
                if match:
                    self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(self.ns_id)
                    self.volume_name = self.nvme_block_device.replace("/dev/", "")
                    fun_test.test_assert_expected(expected=self.volume_name,
                                                  actual=lsblk_output[volume_name]["name"],
                                                  message="{} device available".format(self.volume_name))
                    break
            else:
                fun_test.test_assert(False, "{} device available".format(self.volume_name))

            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["ec"]["nvme_connect"] = True

        # Executing the FIO command to fill the volume to it's capacity
        if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
            fun_test.log("Executing the FIO command to perform sequential write to volume")
            fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                cpus_allowed=self.numa_cpus,
                                                **self.warm_up_fio_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Pre-populating the volume")
            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval), self.iter_interval)

            fun_test.shared_variables["ec"]["warmup_io_completed"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
        self.volume_name = fun_test.shared_variables["volume_name"]

        if "ec" in fun_test.shared_variables or fun_test.shared_variables["ec"]["setup_created"]:
            self.nvme_block_device = fun_test.shared_variables["nvme_block_device"]
            self.volume_name = fun_test.shared_variables["volume_name"]
        else:
            fun_test.simple_assert(False, "Setup Section Status")

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
        # row_data_dict = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_numjobs_iodepth
        fio_result = {}
        fio_output = {}

        for combo in self.fio_numjobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}

            fio_num_jobs, fio_iodepth = eval(combo)

            for mode in self.fio_modes:

                fio_block_size = self.fio_cmd_args["bs"]
                fio_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = fio_iodepth
                size = self.ec_info["capacity"] / (1024 * 3)
                row_data_dict["size"] = str(size) + "G"

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC".
                             format(mode, fio_block_size, fio_iodepth))
                fio_job_name = "{}_{}_{}".format(self.fio_job_name, mode, fio_iodepth * fio_num_jobs)
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                                 rw=mode,
                                                                 numjobs=fio_num_jobs,
                                                                 iodepth=fio_iodepth,
                                                                 name=fio_job_name,
                                                                 cpus_allowed=self.numa_cpus,
                                                                 **self.fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                fun_test.test_assert(fio_output[combo][mode],
                                     "Execute fio '{0}' test with block size:{1}, iodepth: {2} num_jobs: {3}".format(
                                         mode, fio_block_size, fio_iodepth, fio_num_jobs))

                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value))

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

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
                    post_results("Inspur Performance Test", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for combo in self.fio_numjobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode]:
                    test_result = False
        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class EC42FioSeqReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="EC volume performance for sequential Read queries",
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
                              summary="EC volume performance for random read only queries",
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
