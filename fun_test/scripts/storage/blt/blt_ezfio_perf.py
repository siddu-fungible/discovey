from lib.system.fun_test import *

fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.system import utils
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *
import copy
import datetime


def start_mpstat(host_handle, runtime, stats_args):
    mpstat_count = (int(runtime) / stats_args["interval"])
    mpstat_cpu_list = stats_args["cpu_list"]
    fun_test.log("Collecting mpstat ...")
    mpstat_post_fix_name = "ezfio_mpstat.txt"
    mpstat_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=mpstat_post_fix_name)
    mpstat_pid = host_handle.mpstat(cpu_list=mpstat_cpu_list, output_file=stats_args["output_file"],
                                    interval=stats_args["interval"], count=int(mpstat_count))
    return mpstat_artifact_file, mpstat_pid


def stop_mpstat(host_handle, stats_args, mpstat_pid, mpstat_artifact_file):
    mpstat_pid_check = host_handle.get_process_id("mpstat")
    if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid):
        host_handle.kill_process(process_id=int(mpstat_pid_check))
    # Saving the mpstat output to the mpstat_artifact_file file
    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                 source_file_path=stats_args["output_file"],
                 target_file_path=mpstat_artifact_file)
    fun_test.add_auxillary_file(description="Host CPU Usage",
                                filename=mpstat_artifact_file)


def start_funos_stats(sc_dpcsh_obj, vol_details, runtime, interval, stats_list):
    stats_count = (int(runtime) / interval)
    file_suffix = "ezfio_funos_stats.txt"
    for index, stat_detail in enumerate(stats_list):
        func = stat_detail.keys()[0]
        stats_list[index][func]["count"] = int(stats_count)
        if func == "vol_stats":
            stats_list[index][func]["vol_details"] = vol_details
    sc_dpcsh_obj.verbose = False
    stats_obj = CollectStats(sc_dpcsh_obj)
    stats_obj.start(file_suffix, stats_list)
    fun_test.log("FunOS stats collection for the ezfio perf test started: {}".
                 format(stats_list))
    return stats_obj


def stop_funos_stats(sc_dpcsh_obj, stats_obj, stats_list):
    stats_obj.stop(stats_list)
    sc_dpcsh_obj.verbose = True
    job_name = "ezfio_perf"
    stats_obj.populate_stats_to_file(stats_list, job_name)


class EzfioPerfSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        already_deployed = False
        if "already_deployed" in job_inputs:
            already_deployed = job_inputs["already_deployed"]

        dpu_index = None if "num_f1" not in job_inputs else range(job_inputs["num_f1"])

        # TODO: Check workload=storage in deploy(), set dut params
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.sc_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed, dpu_indexes=[0])
        fun_test.shared_variables["storage_controller_template"] = self.sc_template

        # Below lines are needed so that we create/attach volumes only once and other testcases use the same volumes
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False

    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()


class SingleBltSingleHost(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Ezfio test on BLT which will run pre-defined set of iodepth & block sizes",
                              steps='''
        1. Create 1 BLT volume on F1 attached
        2. Create a storage controller for TCP and attach above volume to this controller   
        3. Connect to this volume from remote host
        4. Run ezfio.py script which will run fio underneath with sequential and random workload with 
        pre-conditioning and tests with a set of iodepth and block sizes        
        ''')

    def setup(self):
        fun_test.shared_variables["fio"] = {}
        testcase = self.__class__.__name__

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

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "blt_count"):
            self.blt_count = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "capacity" in job_inputs:
            self.blt_details["capacity"] = job_inputs["capacity"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "runtime" in job_inputs:
            self.fio_cmd_args["runtime"] = job_inputs["runtime"]
            self.fio_cmd_args["timeout"] = self.fio_cmd_args["runtime"] + 15
        if "full_runtime" in job_inputs:
            self.fio_full_run_time = job_inputs["full_runtime"]
            self.fio_full_run_timeout = self.fio_full_run_time + 15
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if (not fun_test.shared_variables["blt"]["setup_created"]):

            self.topology = fun_test.shared_variables["topology"]
            self.sc_template = fun_test.shared_variables["storage_controller_template"]

            fs_obj_list = []
            for dut_index in self.topology.get_available_duts().keys():
                fs_obj = self.topology.get_dut_instance(index=dut_index)
                fs_obj_list.append(fs_obj)
            fs_obj = fs_obj_list[0]
            self.sc_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
            self.hosts = self.topology.get_available_host_instances()

            # Connect to only 1 host for now
            self.host = self.hosts[0]

            # Get Linux instance
            self.host_instance = self.host.get_instance()

            # TODO: Move to a method
            # Copy ezfio script to end host
            ezfio_filename = "ezfio-fungible.tgz"
            ezfio_dir = INTEGRATION_DIR + "/tools/storage/{}".format(ezfio_filename)
            target_install_dir = "/home/localadmin"
            fun_test.scp(source_file_path=ezfio_dir, target_ip=self.host_instance.host_ip,
                         target_username=self.host_instance.ssh_username,
                         target_password=self.host_instance.ssh_password, target_file_path=target_install_dir)
            self.host_instance.sudo_command("tar -zxvf {}/{}".format(target_install_dir, ezfio_filename))
            self.ezfio_host_path = "{}/{}".format(target_install_dir, ezfio_filename.strip(".tgz"))

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.sc_dpcsh_obj)
            if min_drive_capacity:
                self.blt_details["capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                                  "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            self.create_volume_list = []
            drive_id_list = []

            use_unique_drives = True
            if "use_unique_drives" in job_inputs:
                use_unique_drives = job_inputs["use_unique_drives"]
            fun_test.add_checkpoint(
                checkpoint="Check if volumes are to be created in unique drives:{}".format(str(use_unique_drives)))

            for i in range(self.blt_count):
                suffix = utils.generate_uuid(length=4)
                name = "blt_vol_{}_{}".format(suffix, i + 1)
                body_volume_intent_create = BodyVolumeIntentCreate(name=name,
                                                                   vol_type=self.sc_template.vol_type,
                                                                   capacity=self.blt_details["capacity"],
                                                                   compression_effort=False,
                                                                   encrypt=False, data_protection={})

                vol_uuid_list = self.sc_template.create_volume(fs_obj=fs_obj_list,
                                                               body_volume_intent_create=body_volume_intent_create)
                current_vol_uuid = vol_uuid_list[0]
                fun_test.test_assert(expression=vol_uuid_list,
                                     message="Created Volume {} Successful".format(current_vol_uuid))
                self.create_volume_list.append(current_vol_uuid)

                # Check if drive id is unique
                if use_unique_drives:
                    props_tree = "{}/{}/{}".format("storage", "volumes", self.sc_template.vol_type)
                    dpcsh_op = self.sc_dpcsh_obj.peek(props_tree=props_tree)
                    fun_test.simple_assert(current_vol_uuid in dpcsh_op["data"].keys(),
                                           message="Volume {} not seen in peek storage output".format(current_vol_uuid))
                    drive_id = dpcsh_op["data"][current_vol_uuid]["stats"]["drive_uuid"]
                    fun_test.test_assert(drive_id not in drive_id_list,
                                         message="Volume with uuid {} id created on unique drive having"
                                                 " uuid {}".format(current_vol_uuid, drive_id))
                    drive_id_list.append(drive_id)

            fun_test.test_assert_expected(expected=self.blt_count, actual=len(self.create_volume_list),
                                          message="Created {} number of volumes".format(self.blt_count))

            # Attach volumes to hosts and do nvme connect
            self.attach_vol_result = self.sc_template.attach_m_vol_n_host(fs_obj=fs_obj,
                                                                          volume_uuid_list=self.create_volume_list,
                                                                          host_obj_list=[self.host],
                                                                          volume_is_shared=False,
                                                                          raw_api_call=self.raw_api_call,
                                                                          validate_nvme_connect=False)
            fun_test.test_assert(expression=self.attach_vol_result, message="Attached volumes to hosts")
            fun_test.shared_variables["volumes_list"] = self.create_volume_list
            fun_test.shared_variables["attach_volumes_list"] = self.attach_vol_result

            # Test for only 1 host for now
            self.host.nvme_connect_info = {}
            for result in self.attach_vol_result[self.host]:
                if self.raw_api_call:
                    # fun_test.test_assert(expression=result["status"], message="Attach volume {} to {} host".
                    #                     format(i, host.name))
                    subsys_nqn = result["data"]["subsys_nqn"]
                    host_nqn = result["data"]["host_nqn"]
                    dataplane_ip = result["data"]["ip"]
                else:
                    subsys_nqn = result.subsys_nqn
                    host_nqn = result.host_nqn
                    dataplane_ip = result.ip

                if subsys_nqn not in self.host.nvme_connect_info:
                    self.host.nvme_connect_info[subsys_nqn] = []
                host_nqn_ip = (host_nqn, dataplane_ip)
                if host_nqn_ip not in self.host.nvme_connect_info[subsys_nqn]:
                    self.host.nvme_connect_info[subsys_nqn].append(host_nqn_ip)

            # Connect to only 1 host for now
            for subsys_nqn in self.host.nvme_connect_info:
                for host_nqn_ip in self.host.nvme_connect_info[subsys_nqn]:
                    host_nqn, dataplane_ip = host_nqn_ip
                    fun_test.test_assert(
                        expression=self.sc_template.nvme_connect_from_host(host_obj=self.host, subsys_nqn=subsys_nqn,
                                                                           host_nqn=host_nqn,
                                                                           dataplane_ip=dataplane_ip),
                        message="NVMe connect from host: {}".format(self.host.name))
                    nvme_filename = self.sc_template.get_host_nvme_device(host_obj=self.host, subsys_nqn=subsys_nqn)
                    fun_test.test_assert(expression=nvme_filename,
                                         message="Get NVMe drive from Host {} using lsblk".format(self.host.name))

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                set_fcp_scheduler(storage_controller=self.sc_dpcsh_obj,
                                  config_fcp_scheduler=self.config_fcp_scheduler,
                                  command_timeout=5)

            # Check number of volumes and devices found from hosts
            self.host.nvme_block_device_list = []
            nvme_devices = self.sc_template.get_host_nvme_device(host_obj=self.host)

            if nvme_devices:
                if isinstance(nvme_devices, list):
                    for nvme_device in nvme_devices:
                        current_device = nvme_device
                        self.host.nvme_block_device_list.append(current_device)
                else:
                    current_device = nvme_devices
                    self.host.nvme_block_device_list.append(current_device)
            fun_test.test_assert_expected(expected=len(self.attach_vol_result[self.host]),
                                          actual=len(self.host.nvme_block_device_list),
                                          message="Check number of nvme block devices found "
                                                  "on host {} matches with attached ".format(self.host.name))

            # Create fio filename on host
            self.host.fio_filename = ":".join(self.host.nvme_block_device_list)

            fun_test.shared_variables["blt"]["setup_created"] = True
            fun_test.shared_variables["hosts"] = self.hosts
            fun_test.shared_variables["host"] = self.host
            fun_test.shared_variables["dpcsh_obj"] = self.sc_dpcsh_obj
            fun_test.shared_variables["ezfio_host_path"] = self.ezfio_host_path

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.test_mode = testcase[12:]

        self.hosts = fun_test.shared_variables["hosts"]
        self.host = fun_test.shared_variables["host"]
        self.sc_dpcsh_obj = fun_test.shared_variables["dpcsh_obj"]

        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[BltVolumeOperationsTemplate.vol_type] = fun_test.shared_variables["volumes_list"]
        vol_details.append(vol_group)

        end_host_thread = self.host.instance.clone()

        row_data_dict = {}
        file_size_in_gb = self.blt_details["capacity"] / 1073741824
        row_data_dict["size"] = str(file_size_in_gb) + "GB"

        fun_test.log("Running EzFIO...")  # TODO: Improve this log

        fun_test.log("Volume name is: {}".format(self.host.nvme_block_device_list))

        self.ezfio_host_path = fun_test.shared_variables["ezfio_host_path"]

        # Get current datetime to store file in unique locations
        current_str_time = get_current_time().isoformat(sep="_")
        outputdir_name = "{}/{}_{}".format(self.ezfio_host_path, testcase, current_str_time)

        # Get numa nodes to pass to ezfio
        numa_node_to_use = get_device_numa_node(end_host_thread, self.ethernet_adapter)
        if self.host.name.startswith("cab0"):
            host_numa_cpus = ",".join(self.host.spec["cpus"]["numa_node_ranges"])
        else:
            host_numa_cpus = self.host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]

        # Start stats collection
        ezfio_runtime = 5 * 3600
        mpstat_artifact_file, mpstat_pid = \
            start_mpstat(host_handle=end_host_thread, runtime=ezfio_runtime,
                         stats_args=self.mpstat_args)
        stats_obj = start_funos_stats(sc_dpcsh_obj=self.sc_dpcsh_obj, vol_details=vol_details,
                                      runtime=ezfio_runtime, interval=60, stats_list=self.stats_collect_details)
        ezfio_output = ezfio_run(host_handle=end_host_thread,
                                 ezfio_path=self.ezfio_host_path,
                                 device=self.host.nvme_block_device_list[0],
                                 output_dest=outputdir_name,
                                 dev_util=100, host_index=0, cpu_list=host_numa_cpus,
                                 timeout=ezfio_runtime)

        # Stop mpstat logs
        stop_mpstat(host_handle=end_host_thread, stats_args=self.mpstat_args,
                    mpstat_pid=mpstat_pid, mpstat_artifact_file=mpstat_artifact_file)
        # Stop funos stats
        stop_funos_stats(sc_dpcsh_obj=self.sc_dpcsh_obj, stats_obj=stats_obj,
                         stats_list=self.stats_collect_details)

        # Tar details* directory and copy it out
        ezfio_details_dir = end_host_thread.sudo_command(
            "pushd {} > /dev/null; ls -d details_*; popd > /dev/null".format(outputdir_name)
        )
        ezfio_details_dir = str(ezfio_details_dir).strip()
        end_host_thread.sudo_command(
            "pushd {} > /dev/null; tar -zcvf {}.tgz {}; popd > /dev/null".format(outputdir_name, ezfio_details_dir, ezfio_details_dir))

        ezfio_artifact_tarball = fun_test.get_test_case_artifact_file_name(
            post_fix_name="{}_ezfio_detailed_logs.tgz".format(testcase))
        fun_test.scp(source_port=end_host_thread.ssh_port, source_username=end_host_thread.ssh_username,
                     source_password=end_host_thread.ssh_password, source_ip=end_host_thread.host_ip,
                     source_file_path="{}/{}.tgz".format(outputdir_name, ezfio_details_dir),
                     target_file_path=ezfio_artifact_tarball)
        fun_test.add_auxillary_file(description="Ezfio detailed test results (tarball)",
                                    filename=ezfio_artifact_tarball)

        # Collect syslog from host
        syslog_artifact_file = fun_test.get_test_case_artifact_file_name(
            post_fix_name="{}_syslog.txt".format(testcase))
        fun_test.scp(source_port=end_host_thread.ssh_port, source_username=end_host_thread.ssh_username,
                     source_password=end_host_thread.ssh_password, source_ip=end_host_thread.host_ip,
                     source_file_path="/var/log/syslog",
                     target_file_path=syslog_artifact_file)
        fun_test.add_auxillary_file(description="Host syslog", filename=syslog_artifact_file)

        # Check the output of ezfio.py script and collect .ods final report
        fun_test.test_assert("COMPLETED!" in ezfio_output, message="Ezfio completed successful")

        # Copy ezfio output (.ods file)
        ezfio_ods_file = "{}/*.ods".format(outputdir_name)
        if ezfio_ods_file:
            ezfio_artifact_final_report = fun_test.get_test_case_artifact_file_name(
                post_fix_name="{}_ezfio_perf.ods".format(testcase))
            fun_test.scp(source_port=end_host_thread.ssh_port, source_username=end_host_thread.ssh_username,
                         source_password=end_host_thread.ssh_password, source_ip=end_host_thread.host_ip,
                         source_file_path=ezfio_ods_file,
                         target_file_path=ezfio_artifact_final_report)
            fun_test.add_auxillary_file(description="Ezfio final test result: *.ods",
                                        filename=ezfio_artifact_final_report)

    def cleanup(self):
        pass


if __name__ == "__main__":
    setup_bringup = EzfioPerfSetup()
    setup_bringup.add_test_case(SingleBltSingleHost())
    setup_bringup.run()
