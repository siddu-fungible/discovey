from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.utilities.funcp_config import *

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''

def post_results(volume, test, block_size, numjobs, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):

    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volume = fun_test.shared_variables["blt_count"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volume, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))

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

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/raw_vol_pcie_perf.json')
        fun_test.shared_variables["server_key"] = self.server_key

        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
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

        # Add static routes on Containers
        funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
        fun_test.sleep(message="Waiting before ping tests", seconds=10)

        # Ping QFX from both F1s
        ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        for container in ping_dict:
            funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

        # Ping vlan to vlan
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.test_cc_pings_fs()

        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])

        # install drivers on PCIE connected servers
        tb_config_obj = tb_configs.TBConfigs(str(fs_name) + "2")
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, sriov=4, num_queues=4)
        
        # get ethtool output
        get_ethtool_on_hu_host(funeth_obj)
        for server in self.server_key["fs"][fs_name]["vm_config"]:
            critical_log(enable_nvme_vfs
                         (host=server,
                          pcie_vfs_count=self.server_key["fs"][fs_name]["vm_config"][server]["pcie_vfs"]),
                          message="NVMe VFs enabled")
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host])

        # Start VMs
        servers_with_vms = self.server_key["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            configure_vms(server_name=server, vm_dict=servers_with_vms[server]["vms"])

        #fun_test.sleep(message="Waiting for VMs to come up", seconds=120)

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
        testconfig_file = fun_test.get_script_parent_directory() + '/raw_vol_pcie_perf.json'
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
                                                   target_port=40221)
            command_result = storage_controller.ip_cfg(ip=servers_with_vms[server]["local_controller_ip"],
                                               port=servers_with_vms[server]["local_controller_port"])

            fun_test.test_assert(command_result["status"], "Configuring IP {}:{} to storage controller".
                                 format(servers_with_vms[server]["local_controller_ip"],
                                        servers_with_vms[server]["local_controller_port"]))
            result_dict = {}

            for vm in servers_with_vms[server]["vms"]:
                result_dict[vm] = {}
                blt_volume_dpu_1 = utils.generate_uuid()
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

                local_volume_create(storage_controller=storage_controller,
                                    vm_dict=servers_with_vms[server]["vms"][vm]["local_storage"],
                                    uuid=blt_volume_dpu_1, count=i)
                result_dict[vm]["blt_volume_dpu_1"] = blt_volume_dpu_1

                print("\n")
                print("===========================================")
                print("Attach Local Volume to Controller on DPU 1")
                print("===========================================\n")
                command_result = storage_controller.attach_volume_to_controller(ctrlr_uuid=controller_dpu_1,
                                                                        vol_uuid=blt_volume_dpu_1,
                                                                        ns_id=int(i),
                                                                        command_duration=
                                                                        servers_with_vms[server]["vms"][vm][
                                                                            "local_storage"]["command_timeout"])
                fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}"
                             .format(blt_volume_dpu_1, controller_dpu_1))

                # Workaround for connecting to the VM via SSH
                host_obj.sudo_command("sysctl -w net.bridge.bridge-nf-call-iptables=0")

                # Reloading nvme driver on VM
                reload_nvme_driver(host=servers_with_vms[server]["vms"][vm]["hostname"],
                                   username="localadmin",
                                   password="Precious1*")

                # Check if volume exists
                # TODO: Check for vol

                """
                # Get the nvme device name from the VMs
                fun_test.shared_variables["nvme_block_device"] = get_nvme_dev(servers_with_vms[server]["vms"][vm]["hostname"])
                """
                self.nvme_block_device = "/dev/nvme0n1"
                fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
                fun_test.shared_variables["vol_size"] = \
                    int(servers_with_vms[server]["vms"][vm]["local_storage"]["blt_vol_capacity"])
                result_dict[vm]["nvme_block_device"] = fun_test.shared_variables["nvme_block_device"]

                self.end_host = Linux(host_ip=servers_with_vms[server]["vms"][vm]["hostname"],
                                      ssh_username="localadmin",
                                      ssh_password="Precious1*")
                fun_test.shared_variables["end_host_obj"] = self.end_host

                """
                # Run warmup
                if self.warm_up_traffic:
                    fun_test.log(
                        "Initial Write IO to volume, this might take long time depending on fio --size provided")
                    for i in range(0, 2):
                        fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device,
                                                            **self.warm_up_fio_cmd_args)
                        fun_test.test_assert(fio_output, "Pre-populating the volume")
                        fun_test.log("FIO Command Output:\n{}".format(fio_output))

                    fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                                   self.iter_interval)
                """
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

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        self.end_host = fun_test.shared_variables["end_host_obj"]

        for mode in self.fio_modes:
            for combo in self.fio_jobs_iodepth:
                fio_result[combo] = {}
                fio_output[combo] = {}
                internal_result[combo] = {}
                initial_volume_status[combo] = {}
                final_volume_status[combo] = {}
                diff_volume_stats[combo] = {}
                initial_stats[combo] = {}
                final_stats[combo] = {}
                diff_stats[combo] = {}

                tmp = combo.split(',')
                fio_block_size = self.fio_bs
                fio_numjobs = tmp[0].strip('() ')
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                row_data_dict["num_jobs"] = fio_numjobs
                file_size_in_gb = fun_test.shared_variables["vol_size"] / 1073741824
                row_data_dict["size"] = str(file_size_in_gb) + "GB"

                fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                             format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                cpus_allowed = "0-15"

                fun_test.log("Running FIO...")
                fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_filename = fun_test.shared_variables["nvme_block_device"]
                fio_output[combo][mode] = self.end_host.pcie_fio(filename=fio_filename,
                                                                 numjobs=fio_numjobs,
                                                                 rw=mode,
                                                                 bs=fio_block_size,
                                                                 iodepth=fio_iodepth,
                                                                 name=fio_job_name,
                                                                 size=str(file_size_in_gb) + "G",
                                                                 cpus_allowed=cpus_allowed,
                                                                 **self.fio_cmd_args)

                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.test_assert(fio_output[combo][mode], "Fio {} test for numjobs {} & iodepth {}".
                                     format(mode, fio_numjobs, fio_iodepth))

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        row_data_dict[op + field] = value
                        fun_test.log("raw_data[op + field] is: {}".format(row_data_dict[op + field]))

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                #post_results("VM_Raw_Vol_PCIe", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="VM raw vol over PCIe Perf Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass

class LocalSSDVM(RawVolumeLocalPerfTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Read performance for 1 volumes on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Sequential Read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

if __name__ == "__main__":

    bltscript = RawVolumePerfScript()
    bltscript.add_test_case(LocalSSDVM())
    bltscript.run()
