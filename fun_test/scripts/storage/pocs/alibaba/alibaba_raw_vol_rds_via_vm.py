from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from collections import OrderedDict
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.utilities.funcp_config import *
from fun_global import PerfUnit, FunPlatform

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''


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
    model_name = "AlibabaBmvRemoteSsdPerformance"
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
        job_inputs = fun_test.get_job_inputs()
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt syslog=5 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt syslog=5 workload=storage"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        if not job_inputs:
            job_inputs = {}
        if "skip_warmup" in job_inputs:
            skip_warmup = job_inputs["skip_warmup"]
            fun_test.shared_variables["skip_warmup"] = skip_warmup
        else:
            fun_test.shared_variables["skip_warmup"] = False
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
        fs = topology.get_dut_instance(index=0)
        come_obj = fs.get_come()
        come_obj.command("/home/fun/mks/restart_docker_service.sh")

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
        tb_config_obj = tb_configs.TBConfigs(str(fs_name))
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

        # fun_test.sleep(message="Waiting for VMs to come up", seconds=120)

    def cleanup(self):
        fun_test.shared_variables["topology"].cleanup()


class RawVolumeRemotePerfTestcase(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(
            id=1,
            summary="Perf test for remotely attached SSD via F1",
            steps="""
            1. Create a BLT volume on F1_1
            2. Create a RDS controller on F1_1 and attach above BLT to it
            3. Create PCIe controller on F1_0 for the NVMe VF
            4. Create RDS_BLK volume on F1_0 with remote as F1_1
            5. Attach above volume to the PCIe controller created in step 3
            6. Run random read and write fio for numjobs [1, 2, 4, ..., 256]
            """)

    def setup(self):
        testcase = self.__class__.__name__
        testconfig_file = fun_test.get_script_name_without_ext() + ".json"
        self.server_key = fun_test.parse_file_to_json(testconfig_file)
        fs_spec = fun_test.get_asset_manager().get_fs_spec(self.server_key["fs"][fs_name]["fs-name"])

        testconfig_dict = utils.parse_file_to_json(testconfig_file)
        for k, v in testconfig_dict[testcase].iteritems():
            setattr(self, k, v)

        servers_with_vms = self.server_key["fs"][fs_name]["vm_config"]

        for server in servers_with_vms:
            i = 1

            host_obj = Linux(host_ip=str(server),
                             ssh_username=servers_with_vms[server]["user"],
                             ssh_password=servers_with_vms[server]["password"])

            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for service in udev_services:
                service_status = host_obj.systemctl(service_name=service, action="stop")
            #host_obj.command(command="echo 4 | sudo tee /sys/module/nvme/parameters/io_queue_depth ")
            # fun_test.test_assert(service_status, "Stopping {} service".format(service))

            # Configure storage controller for DPU 1 (since we are testing SSD on DPU 1)
            storage_controller_dpu_0 = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                         target_port=servers_with_vms[server]["dpc_port_local"])
            storage_controller_dpu_1 = StorageController(target_ip=fs_spec['come']['mgmt_ip'],
                                                         target_port=servers_with_vms[server]["dpc_port_remote"])

            print("\n")
            print("===================================")
            print("IP cfg for DPU 0 - Local controller")
            print("===================================\n")
            command_result = storage_controller_dpu_0.ip_cfg(ip=servers_with_vms[server]["local_controller_ip"],
                                                             port=servers_with_vms[server]["local_controller_port"])

            fun_test.test_assert(command_result["status"], "Configuring IP {}:{} to storage controller".
                                 format(servers_with_vms[server]["local_controller_ip"],
                                        servers_with_vms[server]["local_controller_port"]))

            print("\n")
            print("===================================")
            print("IP cfg for DPU 1 - Remote controller")
            print("===================================\n")
            command_result = storage_controller_dpu_1.ip_cfg(ip=servers_with_vms[server]["remote_controller_ip"],
                                                             port=servers_with_vms[server]["remote_controller_port"])

            fun_test.test_assert(command_result["status"], "Configuring IP {}:{} to storage controller".
                                 format(servers_with_vms[server]["remote_controller_ip"],
                                        servers_with_vms[server]["remote_controller_port"]))

            result_dict = {}

            for vm in servers_with_vms[server]["vms"]:
                result_dict[vm] = {}

                print servers_with_vms[server]["vms"][vm]["storage"]

                blt_volume_dpu_1 = utils.generate_uuid()

                print("\n")
                print("==============================")
                print("Creating Local Volume on DPU 1")
                print("==============================\n")

                local_volume_create(storage_controller=storage_controller_dpu_1,
                                    vm_dict=servers_with_vms[server]["vms"][vm]["storage"],
                                    uuid=blt_volume_dpu_1, count=i)
                result_dict[vm]["blt_volume_dpu_1"] = blt_volume_dpu_1

                rds_controller_dpu_1 = utils.generate_uuid()
                print("\n")
                print("==================================")
                print("Creating RDS Controller on DPU 1")
                print("==================================\n")
                command_result = storage_controller_dpu_1.create_controller(ctrlr_uuid=rds_controller_dpu_1,
                                                                            ctrlr_type="BLOCK",
                                                                            transport=self.remote_transport,
                                                                            remote_ip=servers_with_vms[server]
                                                                            ["local_controller_ip"],
                                                                            subsys_nqn="nqn" + str(i),
                                                                            host_nqn=servers_with_vms[server]
                                                                            ["local_controller_ip"],
                                                                            port=servers_with_vms[server]
                                                                            ["remote_controller_port"],
                                                                            command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                     format(rds_controller_dpu_1))
                result_dict[vm]["rds_controller_dpu_1"] = rds_controller_dpu_1

                print("\n")
                print("==============================================")
                print("Attach Local Volume to RDS Controller on DPU 1")
                print("==============================================\n")
                command_result = storage_controller_dpu_1.attach_volume_to_controller(ctrlr_uuid=rds_controller_dpu_1,
                                                                                      vol_uuid=blt_volume_dpu_1,
                                                                                      ns_id=int(i),
                                                                                      command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}"
                                     .format(blt_volume_dpu_1, rds_controller_dpu_1))

                pci_controller_dpu_0 = utils.generate_uuid()
                print("\n")
                print("==================================")
                print("Creating PCIe Controller on DPU 0")
                print("==================================\n")
                command_result = storage_controller_dpu_0.create_controller(ctrlr_uuid=pci_controller_dpu_0,
                                                                            transport=self.local_transport,
                                                                            fnid=int(
                                                                                servers_with_vms[server]["vms"][vm]
                                                                                ["fnid"]),
                                                                            ctlid=int(
                                                                                servers_with_vms[server]["ctlid"]),
                                                                            huid=int(servers_with_vms[server]["huid"]),
                                                                            command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating PCI controller with uuid {}".
                                     format(pci_controller_dpu_0))
                result_dict[vm]["pci_controller_dpu_0"] = pci_controller_dpu_0

                rds_blk_vol_dpu_0 = utils.generate_uuid()
                print("\n")
                print("==================================")
                print("Creating RDS BLK Volume on DPU 0")
                print("==================================\n")
                command_result = storage_controller_dpu_0.create_rds_volume(
                    uuid=rds_blk_vol_dpu_0,
                    name="rds-blk-" + str(rds_blk_vol_dpu_0),
                    capacity=servers_with_vms[server]["vms"][vm]["storage"]["rds_vol_capacity"],
                    block_size=servers_with_vms[server]["vms"][vm]["storage"]["rds_vol_block_size"],
                    remote_ip=servers_with_vms[server]["remote_controller_ip"],
                    port=servers_with_vms[server]["remote_controller_port"],
                    remote_nsid=int(i),
                    subsys_nqn="nqn" + str(i),
                    host_nqn=servers_with_vms[server]["local_controller_ip"],
                    command_duration=servers_with_vms[server]["vms"][vm]["storage"]["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating RDS volume with uuid {}".
                                     format(rds_blk_vol_dpu_0))
                result_dict[vm]["rds_blk_vol_dpu_0"] = rds_blk_vol_dpu_0

                print("\n")
                print("===================================================")
                print("Attaching RDS BLK Volume to PCI controller on DPU 0")
                print("===================================================\n")
                command_result = storage_controller_dpu_0.attach_volume_to_controller(ctrlr_uuid=pci_controller_dpu_0,
                                                                                      vol_uuid=rds_blk_vol_dpu_0,
                                                                                      ns_id=int(i) + 1,
                                                                                      command_duration=
                                                                                      self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching PCI controller {} to RDS volume {}".
                                     format(pci_controller_dpu_0, rds_blk_vol_dpu_0))

                # Workaround for connecting to the VM via SSH
                host_obj.sudo_command("sysctl -w net.bridge.bridge-nf-call-iptables=0")

                # Reloading nvme driver on VM
                reload_nvme_driver(host=servers_with_vms[server]["vms"][vm]["hostname"],
                                   username=servers_with_vms[server]["vms"][vm]["user"],
                                   password=servers_with_vms[server]["vms"][vm]["password"],
                                   ns_id=int(i))

                """
                # Get the nvme device name from the VMs
                fun_test.shared_variables["nvme_block_device"] = \
                    get_nvme_dev(servers_with_vms[server]["vms"][vm]["hostname"])
                """
                self.nvme_block_device = "/dev/nvme0n" + str(i)
                fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
                fun_test.shared_variables["vol_size"] = \
                    int(servers_with_vms[server]["vms"][vm]["storage"]["blt_vol_capacity"])
                result_dict[vm]["nvme_block_device"] = fun_test.shared_variables["nvme_block_device"]

                self.vm_obj = Linux(host_ip=servers_with_vms[server]["vms"][vm]["hostname"],
                                    ssh_username="localadmin",
                                    ssh_password="Precious1*")
                fun_test.shared_variables["vm_obj"] = self.vm_obj

                # Run warmup
                skip_warmup = fun_test.shared_variables["skip_warmup"]
                if not skip_warmup:
                    if self.warm_up_traffic:
                        fun_test.log(
                            "Initial Write IO to volume, this might take long time depending on fio --size provided")
                        for i in range(0, 2):
                            fio_output = self.vm_obj.pcie_fio(filename=self.nvme_block_device,
                                                              **self.warm_up_fio_cmd_args)
                            fun_test.test_assert(fio_output, "Pre-populating the volume")
                            fun_test.log("FIO Command Output:\n{}".format(fio_output))

                        fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                                       self.iter_interval)

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

        self.vm_obj = fun_test.shared_variables["vm_obj"]

        for combo in self.fio_jobs_iodepth:
            tmp = combo.split(',')
            fio_block_size = self.fio_bs
            fio_numjobs = tmp[0].strip('() ')
            fio_iodepth = tmp[1].strip('() ')
            fio_result[combo] = {}
            internal_result[combo] = {}
            fio_output[combo] = {}
            initial_volume_status[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            initial_stats[combo] = {}
            final_stats[combo] = {}
            diff_stats[combo] = {}
            for mode in self.fio_modes:
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                value_dict = {}
                value_dict["test"] = mode
                value_dict["block_size"] = fio_block_size
                value_dict["io_depth"] = int(fio_iodepth)
                value_dict["num_threads"] = int(fio_numjobs)
                file_size_in_gb = fun_test.shared_variables["vol_size"] / 1073741824
                value_dict["io_size"] = str(file_size_in_gb) + "GB"
                value_dict["num_ssd"] = 1
                value_dict["num_volume"] = 1
            #for mode in self.fio_modes:

                fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                             format(mode, fio_block_size, fio_numjobs, fio_iodepth))
                cpus_allowed = "0-15"
                fun_test.log("Running FIO...")
                fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_" + \
                               self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_filename = fun_test.shared_variables["nvme_block_device"]
                fio_output[combo][mode] = self.vm_obj.pcie_fio(filename=fio_filename,
                                                               numjobs=fio_numjobs,
                                                               rw=mode,
                                                               bs=fio_block_size,
                                                               iodepth=fio_iodepth,
                                                               name=fio_job_name,
                                                               cpus_allowed=cpus_allowed,
                                                               **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.test_assert(fio_output[combo][mode], "Fio {} test for numjobs {} & iodepth {}".
                                     format(mode, fio_numjobs, fio_iodepth))
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
                for op, stats in fio_output[combo][mode].items():
                    # TODO: "operation" gets overwritten here; Set operation based on mode
                    if op == "read":
                        value_dict["operation"] = op
                        value_dict["read_iops"] = stats["iops"]
                        value_dict["read_throughput"] = int(round(stats["bw"] / 1000))
                        value_dict["read_avg_latency"] = stats["clatency"]
                        value_dict["read_90_latency"] = stats["latency90"]
                        value_dict["read_95_latency"] = stats["latency95"]
                        value_dict["read_99_99_latency"] = stats["latency9999"]
                        value_dict["read_99_latency"] = stats["latency99"]
                    else:
                        value_dict["operation"] = op
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
        fun_test.add_table(panel_header="Ali BMV BLT over RDS Perf Table", table_name=self.summary,
                           table_data=table_data)

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


class RemoteSSDVM(RawVolumeRemotePerfTestcase):

    def describe(self):
        self.set_test_details(
            id=2,
            summary="Random Read/Write performance for 1 volumes over RDS"
                    "with different levels of numjobs & iodepth & block size 4K",
            steps='''
            1. Create a BLT volume on F1_1
            2. Create a RDS controller on F1_1 and attach above BLT to it
            3. Create PCIe controller on F1_0 for the NVMe VF
            4. Create RDS_BLK volume on F1_0 with remote as F1_1
            5. Attach above volume to the PCIe controller created in step 3
            6. Run random read and write fio for numjobs [1, 2, 4, ..., 256]
        ''')


if __name__ == "__main__":
    bltscript = RawVolumePerfScript()
    bltscript.add_test_case(RemoteSSDVM())
    bltscript.run()
