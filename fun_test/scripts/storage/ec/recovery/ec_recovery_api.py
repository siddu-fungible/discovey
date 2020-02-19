from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.system import utils
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *
import copy
import itertools
import random
from copy import deepcopy


class ECBlockRecoveryScript(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        job_inputs = {}
        job_inputs = fun_test.get_job_inputs()

        already_deployed = False
        if "already_deployed" in job_inputs:
            already_deployed = job_inputs["already_deployed"]

        dpu_index = None if not "num_f1" in job_inputs else range(job_inputs["num_f1"])

        # TODO: Check workload=storage in deploy(), set dut params
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.sc_template = EcVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed, dpu_indexes=dpu_index)
        fun_test.shared_variables["storage_controller_template"] = self.sc_template

    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()

class RecoveryWithFailures(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random read performance for muiltple hosts on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
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
        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "num_volumes" in job_inputs:
            self.ec_info["num_volumes"] = job_inputs["num_volumes"]
        if "capacity" in job_inputs:
            self.ec_info["capacity"] = job_inputs["capacity"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "plex_fail_method" in job_inputs:
            self.plex_fail_method = job_inputs["plex_fail_method"]
        if "plex_failure_combination" in job_inputs:
            self.plex_failure_combination = job_inputs["plex_failure_combination"]
        if "test_bs" in job_inputs:
            self.fio_write_cmd_args["bs"] = job_inputs["test_bs"]
            self.fio_read_cmd_args["bs"] = job_inputs["test_bs"]

        #if (not fun_test.shared_variables["ec"]["setup_created"]):

        self.topology = fun_test.shared_variables["topology"]
        self.sc_template = fun_test.shared_variables["storage_controller_template"]

        self.fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)
        fs_obj = self.fs_obj_list[0]
        self.storage_controller_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
        self.hosts = self.topology.get_available_host_instances()

        fun_test.shared_variables["hosts"] = self.hosts
        fun_test.shared_variables["dpcsh_obj"] = self.storage_controller_dpcsh_obj

    def run(self):
        testcase = self.__class__.__name__
        fs_obj = self.fs_obj_list[0]
        for combo in self.ec_list:
            self.ec_info["ndata"] = int(combo.split(",")[0])
            self.ec_info["nparity"] = int(combo.split(",")[1])
            plex_fail_comb_list = []
            if self.plex_failure_combination == "all":
                plex_fail_comb_list = list(
                    itertools.combinations(range(self.ec_info["ndata"] + self.ec_info["nparity"]),
                                           self.ec_info["nparity"]))
            elif self.plex_failure_combination == "random":
                plex_fail_comb_list.append(tuple(random.sample(range(self.ec_info["ndata"] + self.ec_info["nparity"]), self.ec_info["nparity"])))
            for plex_fail_pattern in plex_fail_comb_list:
                #configure ec volume
                self.create_volume_list = []
                for num in range(self.ec_info["num_volumes"]):
                    name = "EC" + testcase + "_" + str(num + 1)
                    body_volume_intent_create = BodyVolumeIntentCreate(name=name,
                                                                       vol_type=self.sc_template.vol_type,
                                                                       capacity=self.ec_info["capacity"],
                                                                       compression_effort=self.ec_info["compression_effort"],
                                                                       allow_expansion=self.ec_info["allow_expansion"],
                                                                       stripe_count=self.ec_info["stripe_count"],
                                                                       encrypt=self.ec_info["encrypt"],
                                                                       data_protection=self.ec_info["data_protection"])

                    vol_uuid_list = self.sc_template.create_volume(fs_obj=fs_obj,
                                                                   body_volume_intent_create=
                                                                   body_volume_intent_create)
                    fun_test.test_assert(expression=vol_uuid_list,
                                         message="Created Volume {} Successful".format(vol_uuid_list[0]))
                    self.create_volume_list.append(vol_uuid_list[0])

                fun_test.test_assert_expected(expected=self.ec_info["num_volumes"], actual=len(self.create_volume_list),
                                              message="Created {} number of volumes".format(self.ec_info["num_volumes"]))
                # From LSV vol uuid, get the EC vol uuid, from which get BLT uuids
                raw_sc_api = StorageControllerApi(api_server_ip=self.storage_controller_dpcsh_obj.target_ip)
                lsv_vol_get = raw_sc_api.execute_api(method="GET", cmd_url="storage/volumes/{}".format(vol_uuid_list[0])).json()
                if lsv_vol_get['status']:
                    lsv_mem_vols_list = lsv_vol_get["data"]["src_vols"]
                for vol_uuid in lsv_mem_vols_list:
                    lsv_mem_vols_get = raw_sc_api.execute_api(method="GET", cmd_url="storage/volumes/{}".format(vol_uuid)).json()
                    if lsv_mem_vols_get["status"]:
                        if lsv_mem_vols_get["data"]["type"] == "VOL_TYPE_BLK_EC":
                            ec_vol_uuid = vol_uuid
                            blt_uuids_list = lsv_mem_vols_get["data"]["src_vols"]
                            break
                        else:
                            continue
                drive_uuid_list = []
                for blt_uuid in blt_uuids_list:
                    blt_uuid_get_result = raw_sc_api.execute_api(method="GET", cmd_url="storage/volumes/{}".format(blt_uuid)).json()
                    if blt_uuid_get_result["status"]:
                        drive_uuid_list.append(blt_uuid_get_result["data"]["stats"]["stats"]["drive_uuid"])
                device_id_list = []
                for drive_uuid in drive_uuid_list:
                    drive_uuid_get_result = raw_sc_api.execute_api(method="GET", cmd_url="topology/drive/{}/slot_id".format(drive_uuid)).json()
                    if drive_uuid_get_result["status"]:
                        device_id_list.append(drive_uuid_get_result["data"]["slot_id"])
                #get_lsv = self.storage_controller_dpcsh_obj.storage_api.get_volume(vol_uuid_list[0])
                # Attach volume to host
                attach_vol_result = self.sc_template.attach_volume(host_obj=self.hosts,
                                                                   fs_obj=fs_obj,
                                                                   volume_uuid=self.create_volume_list[0],
                                                                   validate_nvme_connect=True,
                                                                   raw_api_call=self.raw_api_call,
                                                                   nvme_io_queues=self.nvme_io_queues)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")
                # Get the nvme device list from host
                hosts = self.topology.get_available_hosts()
                self.vol_stats = collections.OrderedDict()
                self.blt_stats_after_initial_read = collections.OrderedDict()
                for host_id in hosts:
                    host_obj = hosts[host_id]
                    nvme_device_name = self.sc_template.get_host_nvme_device(host_obj=host_obj)
                    # Perform initial WRITE
                    fio_output = self.sc_template.traffic_from_host(host_obj=host_obj,
                                                                        filename="/dev/" + nvme_device_name[0],
                                                                        job_name=self.fio_write_cmd_args["name"],
                                                                        numjobs=self.fio_write_cmd_args["numjobs"],
                                                                        iodepth=self.fio_write_cmd_args["iodepth"],
                                                                        rw=self.fio_write_cmd_args["rw"],
                                                                        runtime=60, bs=self.fio_write_cmd_args["bs"],
                                                                        ioengine="libaio", direct=1,
                                                                        time_based=False, norandommap=True,
                                                                        verify=self.fio_write_cmd_args["verify"],
                                                                        do_verify=self.fio_write_cmd_args["do_verify"]
                                                                        )
                    fun_test.test_assert(expression=fio_output,
                                         message="Host : {} FIO traffic result after initial WRITE".format(host_obj.name))
                    fun_test.log(fio_output)
                    self.vol_stats["vol_stats_before_initial_read"] = raw_sc_api.execute_api(method="GET", cmd_url="storage/volumes/{}/stats".format(ec_vol_uuid)).json()
                    # Perform initial READ
                    fio_output = self.sc_template.traffic_from_host(host_obj=host_obj,
                                                                    filename="/dev/" + nvme_device_name[0],
                                                                    job_name=self.fio_read_cmd_args["name"],
                                                                    numjobs=self.fio_read_cmd_args["numjobs"],
                                                                    iodepth=self.fio_read_cmd_args["iodepth"],
                                                                    rw=self.fio_read_cmd_args["rw"],
                                                                    runtime=60, bs=self.fio_read_cmd_args["bs"],
                                                                    ioengine="libaio", direct=1,
                                                                    time_based=False, norandommap=True,
                                                                    verify=self.fio_read_cmd_args["verify"],
                                                                    do_verify=self.fio_read_cmd_args["do_verify"]
                                                                    )
                    fun_test.test_assert(expression=fio_output,
                                         message="Host : {} FIO traffic result after initial READ".format(host_obj.name))
                    fun_test.log(fio_output)
                    self.vol_stats["vol_stats_after_initial_read"] = raw_sc_api.execute_api(method="GET", cmd_url="storage/volumes/{}/stats".format(ec_vol_uuid)).json()
                    EC_vol_stats_after_initial_read = self.vol_stats["vol_stats_after_initial_read"]["data"]["stats"]["stats"]
                    fun_test.log("EC Volume stats:\n{}".format(EC_vol_stats_after_initial_read))
                    # Validate if no READs with data integrity failed
                    fun_test.log("EC volume recovery_read_count: {} and plex_read_fail_count: {}".format(
                        EC_vol_stats_after_initial_read["recovery_read_count"],
                        EC_vol_stats_after_initial_read["plex_read_fail_count"]))
                    fun_test.test_assert_expected(expected=(0, 0),
                                                  actual=(EC_vol_stats_after_initial_read["recovery_read_count"],
                                                          EC_vol_stats_after_initial_read["plex_read_fail_count"]),
                                                  message="Before plex failure, recovery_read_count and plex_read_fail_count of EC volume is 0")
                    # Collect blt stats after initial read
                    for blt_uuid in blt_uuids_list:
                        self.blt_stats_after_initial_read[blt_uuid] = raw_sc_api.execute_api(method="GET",
                                                                                             cmd_url="storage/volumes/{}/stats".format(
                                                                                              blt_uuid)).json()

    def cleanup(self):
        pass

class RecoveryWithMFailure(RecoveryWithFailures):

    """
    def __init__(self):
        testcase = self.__class__.__name__
        #self.sc_lock = Lock()
        #self.syslog = fun_test.shared_variables["syslog"]

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
    """
    def describe(self):
        self.set_test_details(id=1,
                              summary="EC recovery with M plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithMFailure, self).setup()

    def run(self):
        super(RecoveryWithMFailure, self).run()

    def cleanup(self):
        super(RecoveryWithMFailure, self).cleanup()


if __name__ == "__main__":
    ecrecovery = ECBlockRecoveryScript()
    ecrecovery.add_test_case(RecoveryWithMFailure())
    #ecrecovery.add_test_case(RecoveryWithMplus1Failure())
    #ecrecovery.add_test_case(RecoveryWithMConcurrentFailure())
    #ecrecovery.add_test_case(RecoveryWithMplusConcurrentFailure())
    #ecrecovery.add_test_case(RecoveryWithKplusMConcurrentFailure())
    ecrecovery.run()