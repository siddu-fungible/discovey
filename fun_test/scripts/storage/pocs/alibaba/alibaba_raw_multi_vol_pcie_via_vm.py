from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.utilities.funcp_config import *
from fun_global import PerfUnit, FunPlatform

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(value_dict):
    unit_dict = {
        "write_iops_unit": PerfUnit.UNIT_OPS,
        "read_iops_unit": PerfUnit.UNIT_OPS,
        "write_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
        "read_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
        "write_avg_latency_unit": PerfUnit.UNIT_USECS,
        "write_90_latency_unit": PerfUnit.UNIT_USECS,
        "write_95_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_avg_latency_unit": PerfUnit.UNIT_USECS,
        "read_90_latency_unit": PerfUnit.UNIT_USECS,
        "read_95_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_latency_unit": PerfUnit.UNIT_USECS
    }

    value_dict["date_time"] = get_data_collection_time()
    value_dict["volume_type"] = "BLT"
    value_dict["platform"] = FunPlatform.F1
    value_dict["version"] = fun_test.get_version()
    model_name = "AlibabaPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))


class RawVolumePerfScript(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(
            steps=""" 
            1. Get the config for FS 
            2. Bringup both F1s
            3. Bringup FunCP
            4. Create MPG Interfaces and assign static IPs
            """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_name_without_ext() + ".json")
        fun_test.shared_variables["server_key"] = self.server_key

        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt  syslog=5  workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt  syslog=5  workload=storage"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        # fs_name = "fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.cleanup_funcp()
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        servers_list = []

        for server in servers_mode:
            print server
            shut_all_vms(hostname=server)
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Bringup FunCP

        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        # Assign MPG IPs from dhcp
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
            self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
            self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]

        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")


        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])

        for server in self.server_key["fs"][fs_name]["vm_config"]:
            # install drivers on PCIE connected servers
            tb_config_obj = tb_configs.TBConfigs(str(fs_name) + "2")
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=False, sriov=4, num_queues=4)

        #get ethtool output

            get_ethtool_on_hu_host(funeth_obj)
        for server in self.server_key["fs"][fs_name]["vm_config"]:
            critical_log(enable_nvme_vfs
                         (host=server,
                          pcie_vfs_count=self.server_key["fs"][fs_name]["vm_config"][server]["pcie_vfs"]),
                         message="NVMe VFs enabled")

        # Start VMs
        servers_with_vms = self.server_key["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            configure_vms(server_name=server, vm_dict=servers_with_vms[server]["vms"])

            fun_test.sleep(message="Waiting for VMs to come up", seconds=30)

    def cleanup(self):
        fun_test.shared_variables["topology"].cleanup()


class RawVolumeLocalPerfTestcase(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(
            id=1,
            summary="Perf test for locally attached F1 over PCIe",
            steps="""
            1. Create a BLT volume on F1_1
            2. Attach it to NVMe VF on the PCIe attached x86 
            3. Run random read fio for numjobs [1, 2, 4, ..., 256]
            """)

    def setup(self):
        testcase = self.__class__.__name__
        testconfig_file = fun_test.get_script_name_without_ext() + ".json"
        self.server_key = fun_test.parse_file_to_json(testconfig_file)
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.server_key["fs"][fs_name]["fs-name"])

        servers_with_vms = self.server_key["fs"][fs_name]["vm_config"]

        testconfig_dict = utils.parse_file_to_json(testconfig_file)

        for k, v in testconfig_dict[testcase].iteritems():
            setattr(self, k, v)

        host_obj = Linux(host_ip=self.server_key["fs"][fs_name]["hu_host"][0],
                         ssh_username="localadmin",
                         ssh_password="Precious1*")

        for server in servers_with_vms:
            i = 1
            # Configure storage controller for DPU 1 (since we are testing SSD on DPU 1)
            storage_controller = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                   target_port=servers_with_vms[server]["dpc_port_remote"])

            result_dict = {}


            for vm in servers_with_vms[server]["vms"]:
                result_dict[vm] = {}
                blt_volume_dpu_1 = {}
                controller_dpu_1 = utils.generate_uuid()
                print("\n")
                print("==================================")
                print("Creating PCIe Controller on DPU 1")
                print("==================================\n")
                print servers_with_vms[server]["vms"][vm]["local_storage"]
                command_result = storage_controller.create_controller(ctrlr_uuid=controller_dpu_1,
                                                                      transport="PCI",
                                                                      fnid=int(servers_with_vms[server]["vms"][vm][
                                                                                   "fnid"]),
                                                                      ctlid=int(servers_with_vms[server]["ctlid"]),
                                                                      huid=int(servers_with_vms[server]["huid"]),
                                                                      command_duration=servers_with_vms[server]["vms"][
                                                                          vm]["local_storage"]["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                     format(controller_dpu_1))
                result_dict[vm]["controller_dpu_1"] = controller_dpu_1

                print("\n")
                print("==============================")
                print("Creating Local Volume on DPU 1")
                print("==============================\n")

                for x in range(1, self.num_ssds + 1, 1):
                    blt_volume_dpu_1[x] = utils.generate_uuid()
                    local_volume_create(storage_controller=storage_controller,
                                    vm_dict=servers_with_vms[server]["vms"][vm]["local_storage"],
                                    uuid=blt_volume_dpu_1[x], count=x)
                    result_dict[vm]["blt_volume_dpu_1"] = blt_volume_dpu_1


                print("\n")
                print("===========================================")
                print("Attach Local Volume to Controller on DPU 1")
                print("===========================================\n")
                command_timeout = servers_with_vms[server]["vms"][vm]["local_storage"]["command_timeout"]
                for x in range(1, self.num_ssds + 1, 1):
                    command_result = storage_controller.attach_volume_to_controller(ctrlr_uuid=controller_dpu_1,
                                                                                vol_uuid=blt_volume_dpu_1[x],
                                                                                ns_id=int(i),
                                                                                command_duration=command_timeout)
                    i += 1
                    fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}"
                                     .format(blt_volume_dpu_1[x], controller_dpu_1))


                # Workaround for connecting to the VM via SSH
                host_obj.sudo_command("sysctl -w net.bridge.bridge-nf-call-iptables=0")

                # Reloading nvme driver on VM
                reload_nvme_driver(host=servers_with_vms[server]["vms"][vm]["hostname"],
                                   username="localadmin",
                                   password="Precious1*")

                # Check if volume exists
                # TODO: Check for vol

                # Get the nvme device name from the VMs
                fun_test.shared_variables["vol_size"] = \
                    int(servers_with_vms[server]["vms"][vm]["local_storage"]["blt_vol_capacity"])
                self.end_host = Linux(host_ip=servers_with_vms[server]["vms"][vm]["hostname"],
                                      ssh_username="localadmin",
                                      ssh_password="Precious1*")
                device = self.end_host.command("sudo nvme list -o normal | awk -F ' ' '{print $1}' | grep -i nvme0"). \
                    replace("\r", '')
                self.nvme_block_device = device.replace("\n", ":").rstrip(":")
                fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
                result_dict[vm]["nvme_block_device"] = fun_test.shared_variables["nvme_block_device"]

        #Run warmup
        nvmedisk = "/dev/nvme0n"
        ns_id = 1
        fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
        if self.warm_up_traffic:
            for index, host in enumerate(self.server_dict):
                self.end_host = Linux(host_ip=host,
                                      ssh_username="localadmin",
                                      ssh_password="Precious1*")
                counter = 1
                for i in range(0, 4):
                    fio_output = self.end_host.pcie_fio(filename=nvmedisk+ str(ns_id),**self.warm_up_fio_cmd_args)
                    fun_test.test_assert(fio_output, "Pre-populating the volume")
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    counter +=1
                    if i == 1:
                        ns_id += 1
                    if i == 3:
                        counter = 0
                    if counter == 0:
                        ns_id = 1
                        break
                fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                               self.iter_interval)
        else:
            thread_id = {}
            fun_test.shared_variables["fio"] = {}
            fio_filename = fun_test.shared_variables["nvme_block_device"]
            for i in range(0, 2):
                for index, host in enumerate(self.server_dict):
                    self.host = Linux(host_ip=host, ssh_username=self.uname, ssh_password=self.pwd)
                    thread_id[index] = fun_test.execute_thread_after(time_in_seconds=10,
                                        func=fio_parser,
                                        arg1=self.host,
                                        host_index=index,
                                        filename=fio_filename,
                                        **self.warm_up_fio_cmd_args)
                fun_test.sleep("Fio threadzz", seconds=1)
                #fio_output[fio_iodepth] = {}
                for index, host in enumerate(self.server_dict):
                    #fio_output[fio_iodepth][host] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host,
                                                                       fun_test.shared_variables["fio"][index]))

        i += 1

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[3:]
        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_status = {}
        final_volume_status = {}
        diff_volume_stats = {}
        initial_stats = {}
        final_stats = {}
        diff_stats = {}
        fun_test.shared_variables["fio"] = {}

        table_data_headers = ["Block Size", "IO Depth", "Numjobs", "Size", "Test", "Operation",
                              "Write IOPS", "Read IOPS", "Write Throughput in MB/s", "Read Throughput in MB/s",
                              "Avg Write Latency in uSecs", "Write Latency 90 Percentile in uSecs",
                              "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Avg Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs",
                              "Read Latency 99 Percentile in uSecs", "Read Latency 99.99 Percentile in uSecs"]
        table_data_cols = ["block_size", "io_depth", "num_threads", "io_size", "test", "operation",
                           "write_iops", "read_iops", "write_throughput", "read_throughput",
                           "write_avg_latency", "write_90_latency", "write_95_latency",
                           "write_99_latency", "write_99_99_latency",
                           "read_avg_latency", "read_90_latency", "read_95_latency",
                           "read_99_latency", "read_99_99_latency"]
        table_data_rows = []

        for mode in self.fio_modes:
            fio_result[mode] = {}
            internal_result[mode] = {}
            fio_output[mode] = {}
            initial_volume_status[mode] = {}
            final_volume_status[mode] = {}
            diff_volume_stats[mode] = {}
            initial_stats[mode] = {}
            final_stats[mode] = {}
            diff_stats[mode] = {}
            aggr_fio_output = {}
            for combo in self.fio_jobs_iodepth:
                thread_id = {}
                tmp = combo.split(',')
                fio_block_size = self.fio_bs
                fio_numjobs = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')
                fio_result[mode][combo] = True
                internal_result[mode][combo] = True
                aggr_fio_output[fio_iodepth] = {}
                value_dict = {}
                value_dict["test"] = mode
                value_dict["block_size"] = fio_block_size
                value_dict["io_depth"] = int(fio_iodepth)
                value_dict["num_threads"] = int(fio_numjobs)
                file_size_in_gb = fun_test.shared_variables["vol_size"] / 1073741824
                value_dict["io_size"] = str(file_size_in_gb) + "GB"
                value_dict["num_ssd"] = 4
                value_dict["num_volume"] = 4

                fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                             format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                cpus_allowed = "0-15"
                fun_test.log("Running FIO...")
                fio_job_name = "fio_pcie_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + \
                               self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[mode][combo] = {}
                fio_filename = fun_test.shared_variables["nvme_block_device"]
                for index, host in enumerate(self.server_dict):
                    self.host = Linux(host_ip=host, ssh_username=self.uname, ssh_password=self.pwd)
                    thread_id[index] = fun_test.execute_thread_after(time_in_seconds=10,
                                                                            func=fio_parser,
                                                                            arg1=self.host,
                                                                            host_index=index,
                                                                            filename=fio_filename,
                                                                            rw=mode,
                                                                            numjobs=fio_numjobs,
                                                                            bs=fio_block_size,
                                                                            iodepth=fio_iodepth,
                                                                            name=fio_job_name,
                                                                            cpus_allowed=cpus_allowed,
                                                                            **self.fio_cmd_args)
                    fun_test.sleep("Fio threadzz", seconds=1)
                fio_output[fio_iodepth] = {}
                for index, host in enumerate(self.server_dict):
                    fio_output[fio_iodepth][host] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host,
                                                                           fun_test.shared_variables["fio"][index]))

                # Summing up the FIO stats from all the hosts
                for index, host in enumerate(self.server_dict):
                    fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                         "FIO {} test with the Block Size {} IO depth {} and Numjobs {} on {}"
                                         .format(mode, fio_block_size, fio_iodepth, fio_numjobs , host))
                    for op, stats in fun_test.shared_variables["fio"][index].items():
                        if op not in aggr_fio_output[fio_iodepth]:
                            aggr_fio_output[fio_iodepth][op] = {}
                        aggr_fio_output[fio_iodepth][op] = Counter(aggr_fio_output[fio_iodepth][op]) + \
                                                       Counter(fun_test.shared_variables["fio"][index][op])

                fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output[fio_iodepth]))
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
                for op, stats in aggr_fio_output[fio_iodepth].items():
                    for field, value in stats.items():
                        if "latency" in field:
                            #change divide by 2 by number of VMs involved
                            aggr_fio_output[fio_iodepth][op][field] = int(round(value) / 2)
                fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[fio_iodepth]))

                #for op, stats in fio_output[mode][combo].items():
                for op, stats in aggr_fio_output[fio_iodepth].items():
                    # TODO: "operation" gets overwritten here; Set operation based on mode
                    value_dict["operation"] = op
                    if op == "read":
                        value_dict["read_iops"] = stats["iops"]
                        value_dict["read_throughput"] = int(round(stats["bw"] / 1000))
                        value_dict["read_avg_latency"] = stats["clatency"]
                        value_dict["read_90_latency"] = stats["latency90"]
                        value_dict["read_95_latency"] = stats["latency95"]
                        value_dict["read_99_99_latency"] = stats["latency9999"]
                        value_dict["read_99_latency"] = stats["latency99"]
                    else:
                        value_dict["write_iops"] = stats["iops"]
                        value_dict["write_throughput"] = int(round(stats["bw"] / 1000))
                        value_dict["write_avg_latency"] = stats["clatency"]
                        value_dict["write_90_latency"] = stats["latency90"]
                        value_dict["write_95_latency"] = stats["latency95"]
                        value_dict["write_99_99_latency"] = stats["latency9999"]
                        value_dict["write_99_latency"] = stats["latency99"]

                row_data_list = []
                for i in table_data_cols:
                    if i not in value_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(value_dict[i])
                table_data_rows.append(row_data_list)

                post_results(value_dict)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Ali BMV BLT over PCIe Perf Table", table_name=self.summary,
                           table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[mode][combo] or not internal_result[mode][combo]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class LocalSSDVM(RawVolumeLocalPerfTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read/Write performance for 4 volumes on PCIe "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 4 BLT volumes on F1 attached
        2. Create a storage controller for PCIe and attach above volumes to this controller   
        3. Pass this associated PF to a VM on the PCIe attached host
        4. Run the FIO Random Read & Write test(without verify) for block size of 4k and IO depth from the 
        host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":
    bltscript = RawVolumePerfScript()
    bltscript.add_test_case(LocalSSDVM())
    bltscript.run()
