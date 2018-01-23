from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
import uuid

'''
Script to track the performance of various read write combination of replica volume using FIO
'''

topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        },
        1: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        },
        2: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
        }
    }
}


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 3 POSIMs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

        dut_instance = []
        dut_instance.append(topology.get_dut_instance(index=0))
        fun_test.test_assert(dut_instance[0], "Retrieved dut instance 0")

        dut_instance.append(topology.get_dut_instance(index=1))
        fun_test.test_assert(dut_instance[1], "Retrieved dut instance 1")

        dut_instance.append(topology.get_dut_instance(index=2))
        fun_test.test_assert(dut_instance[2], "Retrieved dut instance 2")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        stat_uuids = []
        thin_uuids = []
        rds_uuids = []
        volume_details = []

        command_timeout = 5

        # Volume details for the first F1
        volume_details.append({"ns_id": 1, "type": "VOL_TYPE_BLK_LOCAL_THIN", "capacity": 1073741824,
                               "block_size": 4096, "name": "thin-block1"})
        # Volume details for the second F1
        volume_details.append({"ns_id": 1, "type": "VOL_TYPE_BLK_LOCAL_THIN", "capacity": 1073741824,
                               "block_size": 4096, "name": "thin-block2"})
        # Volume details for the third F1
        volume_details.append({"ns_id": 1, "type": "VOL_TYPE_BLK_REPLICA", "capacity": 1073741824,
                               "block_size": 4096, "name": "replica1"})

        # Configuring the local thin block volume in the first two DUTs and attaching/exporting them to the third one
        for index, dut in enumerate(dut_instance[:-1]):
            storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)

            command_result = {}
            command_result = storage_controller.command("enable_counters")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance {}".format(index))

            command_result = {}
            command_result = storage_controller.ip_cfg(ip=dut.data_plane_ip, expected_command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT instance {}".format(dut.data_plane_ip,
                                                                                                 index))

            command_result = {}
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            thin_uuids.append(this_uuid)
            stat_uuids.append(this_uuid)
            command_result = storage_controller.create_thin_block_volume(capacity=volume_details[index]["capacity"],
                                                                         block_size=volume_details[index]["block_size"],
                                                                         name=volume_details[index]["name"],
                                                                         uuid=this_uuid,
                                                                         expected_command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create {} on Dut Instance {}".
                                 format(volume_details[index]["type"], index))

            command_result = {}
            command_result = storage_controller.attach_volume(ns_id=volume_details[index]["ns_id"], uuid=this_uuid,
                                                              remote_ip=dut_instance[-1].data_plane_ip,
                                                              expected_command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "attach volume on Dut Instance {}".format(index))

        # Binding the local thin block volume from the first two DUTs with RDS volumes in the third DUT
        fun_test.add_checkpoint("Importing volumes on DUT {}".format(len(dut_instance) - 1))
        storage_controller = StorageController(target_ip=dut_instance[-1].host_ip,
                                               target_port=dut_instance[-1].external_dpcsh_port)

        command_result = {}
        command_result = storage_controller.command("enable_counters")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance 2")

        command_result = {}
        command_result = storage_controller.ip_cfg(ip=dut_instance[-1].data_plane_ip,
                                                   expected_command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg {} on Dut Instance {}".
                             format(dut_instance[-1].data_plane_ip, (len(dut_instance) - 1)))

        for index, dut in enumerate(dut_instance[:-1]):
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            rds_uuids.append(this_uuid)
            command_result = {}
            command_result = storage_controller.create_rds_volume(capacity=volume_details[index]["capacity"],
                                                                  block_size=volume_details[index]["block_size"],
                                                                  name=volume_details[index]["name"], uuid=this_uuid,
                                                                  remote_nsid=volume_details[index]["ns_id"],
                                                                  remote_ip=dut_instance[index].data_plane_ip,
                                                                  expected_command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create RDS volume for DUT instance {}".format(index))

        # Configuring replica volume and attaching the above two RDS volumes as its plex
        replica_uuid = str(uuid.uuid4()).replace("-", "")[:10]
        stat_uuids.append(replica_uuid)
        command_result = {}
        command_result = storage_controller.create_replica_volume(capacity=volume_details[-1]["capacity"],
                                                                  uuid=replica_uuid,
                                                                  block_size=volume_details[-1]["block_size"],
                                                                  name=volume_details[-1]["name"], pvol_id=rds_uuids,
                                                                  expected_command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create Replica volume on DUT {}".
                             format((len(dut_instance) - 1)))

        # Attaching/Exporting the Replica volume to the external server
        command_result = {}
        command_result = storage_controller.attach_volume(ns_id=volume_details[-1]["ns_id"], uuid=replica_uuid,
                                                          remote_ip=linux_host.internal_ip,
                                                          expected_command_duration=command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Attaching replica volume on DUT instance 2")

        # disabling the error_injection for the replica volume
        command_result = {}
        command_result = storage_controller.command("poke params/repvol/error_inject 0")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Disabling error_injection on DUT instance 2")

        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
        command_result = {}
        command_result = storage_controller.command("peek params/repvol")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT instance 2")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")

        command_result = {}
        command_result = storage_controller.command("peek storage/volumes")
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Peeking storage volume stats")

        fun_test.test_assert_expected(actual=len(command_result["data"]["VOL_TYPE_BLK_RDS"].keys()),
                                      expected=len(rds_uuids), message="Ensure RDS volumes are found ")
        fun_test.test_assert_expected(actual=len(command_result["data"]["VOL_TYPE_BLK_REPLICA"].keys()),
                                      expected=1, message="Ensure Replica volumes are found ")

        fun_test.shared_variables["dut_instance"] = dut_instance
        fun_test.shared_variables["stat_uuids"] = stat_uuids
        fun_test.shared_variables["thin_uuids"] = thin_uuids
        fun_test.shared_variables["rds_uuids"] = rds_uuids
        fun_test.shared_variables["volume_details"] = volume_details

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class FioSeqWriteSeqReadOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
           a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
           b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__
        dut_instance = fun_test.shared_variables["dut_instance"]
        stat_uuids = fun_test.shared_variables["stat_uuids"]
        thin_uuids = fun_test.shared_variables["thin_uuids"]
        rds_uuids = fun_test.shared_variables["rds_uuids"]
        volume_details = fun_test.shared_variables["volume_details"]

        topology = fun_test.shared_variables["topology"]
        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        # Initializing fio_bs_iodepth variable as a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size

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

        # Setting the list of block size and IO depth combo
        fio_bs_iodepth = []
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        fio_bs_iodepth = benchmark_dict[testcase]['fio_bs_iodepth']
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, fio_bs_iodepth))

        fio_size = "16m"
        fio_timeout = 180
        fio_modes = ['write', 'read']

        # Setting expected FIO results
        expected_fio_result = {}
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))
        expected_fio_result = benchmark_dict[testcase]['expected_fio_result']
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, expected_fio_result))

        if len(fio_bs_iodepth) != len(expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        expected_volume_stats = benchmark_dict[testcase]['expected_volume_stats']
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, expected_volume_stats))

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        internal_result = {}
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        for combo in fio_bs_iodepth:
            fio_result[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            fio_output[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            for mode in fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats from all the 3 DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the 3 DUTs in dictionary format")
                initial_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    initial_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                           format(index))
                    initial_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the beginning of the test in DUT instance {}:".format(index))
                    fun_test.log(initial_volume_status[combo][mode][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling the volume stats from all the three DUTs after the FIO test
                fun_test.log("Pulling the volume stats from all the 3 DUTs after the FIO test")
                final_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    final_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".
                                           format(index))
                    final_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the end of the test in DUT instance {}:".format(index))
                    fun_test.log(final_volume_status[combo][mode][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for index in range(len(dut_instance)):
                    diff_volume_stats[combo][mode][index] = {}
                    for key, value in final_volume_status[combo][mode][index].items():
                        if key in initial_volume_status[combo][mode][index]:
                            diff_volume_stats[combo][mode][index][key] = final_volume_status[combo][mode][index][key] -\
                                                                          initial_volume_status[combo][mode][index][key]
                    fun_test.log("Difference of volume status before and after the test in DUT instance {}:".
                                 format(index))
                    fun_test.log(diff_volume_stats[combo][mode][index])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        if actual < (value * (1 - pass_threshold)):
                            fio_result[combo][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + pass_threshold)):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for index in range(len(dut_instance)):
                    for key in expected_volume_stats[mode].keys():
                        if key in diff_volume_stats[combo][mode][index]:
                            if mode == "read" and index != 2:
                                expected = expected_volume_stats[mode][key] / 2
                            else:
                                expected = expected_volume_stats[mode][key]
                            if diff_volume_stats[combo][mode][index][key] != expected:
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is not equal to the expected value {} in DUT "
                                                  "instance {}".format(key, diff_volume_stats[combo][mode][index][key],
                                                                       expected, index))
                            else:
                                fun_test.log("Final {} value {} is equal to the expected value {} in DUT instance {}".
                                             format(key, diff_volume_stats[combo][mode][index][key], expected, index))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in volume status in DUT instance {}".format(key, index))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in fio_bs_iodepth:
            for mode in fio_modes:
                fun_test.test_assert(fio_result[combo][mode], "FIO {} performance check for the block size & IO depth "
                                                              "combo {}".format(mode, combo))
                fun_test.test_assert(internal_result[combo][mode], "Volume stats check for the {} test for the block "
                                                                   "size & IO depth combo {}".format(mode, combo))


class FioRandWriteRandReadOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Write & Read only performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__
        dut_instance = fun_test.shared_variables["dut_instance"]
        stat_uuids = fun_test.shared_variables["stat_uuids"]
        thin_uuids = fun_test.shared_variables["thin_uuids"]
        rds_uuids = fun_test.shared_variables["rds_uuids"]
        volume_details = fun_test.shared_variables["volume_details"]

        topology = fun_test.shared_variables["topology"]
        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        # Initializing fio_bs_iodepth variable as a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size

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

        # Setting the list of block size and IO depth combo
        fio_bs_iodepth = []
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        fio_bs_iodepth = benchmark_dict[testcase]['fio_bs_iodepth']
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, fio_bs_iodepth))

        fio_size = "16m"
        fio_timeout = 300
        fio_modes = ['randwrite', 'randread']

        # Setting expected FIO results
        expected_fio_result = {}
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))
        expected_fio_result = benchmark_dict[testcase]['expected_fio_result']
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, expected_fio_result))

        if len(fio_bs_iodepth) != len(expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        expected_volume_stats = benchmark_dict[testcase]['expected_volume_stats']
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, expected_volume_stats))

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write & read
        # only modes
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        for combo in fio_bs_iodepth:
            fio_result[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            fio_output[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            for mode in fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats from all the 3 DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the 3 DUTs in dictionary format")
                initial_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    initial_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                           format(index))
                    initial_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the beginning of the test in DUT instance {}:".format(index))
                    fun_test.log(initial_volume_status[combo][mode][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling the volume stats from all the three DUTs after the FIO test
                fun_test.log("Pulling the volume stats from all the 3 DUTs after the FIO test")
                final_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    final_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".
                                           format(index))
                    final_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the end of the test in DUT instance {}:".format(index))
                    fun_test.log(final_volume_status[combo][mode][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for index in range(len(dut_instance)):
                    diff_volume_stats[combo][mode][index] = {}
                    for key, value in final_volume_status[combo][mode][index].items():
                        if key in initial_volume_status[combo][mode][index]:
                            diff_volume_stats[combo][mode][index][key] = final_volume_status[combo][mode][index][key] -\
                                                                          initial_volume_status[combo][mode][index][key]
                    fun_test.log("Difference of volume status before and after the test in DUT instance {}:".
                                 format(index))
                    fun_test.log(diff_volume_stats[combo][mode][index])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        if actual < (value * (1 - pass_threshold)):
                            fio_result[combo][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + pass_threshold)):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for index in range(len(dut_instance)):
                    for key in expected_volume_stats[mode].keys():
                        if key in diff_volume_stats[combo][mode][index]:
                            if mode == "randread" and index != 2:
                                expected = expected_volume_stats[mode][key] / 2
                            else:
                                expected = expected_volume_stats[mode][key]
                            if diff_volume_stats[combo][mode][index][key] != expected:
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is not equal to the expected value {} in DUT "
                                                  "instance {}".format(key, diff_volume_stats[combo][mode][index][key],
                                                                       expected, index))
                            else:
                                fun_test.log("Final {} value {} is equal to the expected value {} in DUT instance {}".
                                             format(key, diff_volume_stats[combo][mode][index][key], expected, index))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in volume status in DUT instance {}".format(key, index))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in fio_bs_iodepth:
            for mode in fio_modes:
                fun_test.test_assert(fio_result[combo][mode], "FIO {} performance check for the block size & IO depth "
                                                              "combo {}".format(mode, combo))
                fun_test.test_assert(internal_result[combo][mode], "Volume stats check for the {} test for the block "
                                                                   "size & IO depth combo {}".format(mode, combo))


class FioSeqReadWriteMix(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential 75% Write & 25% Read performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__
        dut_instance = fun_test.shared_variables["dut_instance"]
        stat_uuids = fun_test.shared_variables["stat_uuids"]
        thin_uuids = fun_test.shared_variables["thin_uuids"]
        rds_uuids = fun_test.shared_variables["rds_uuids"]
        volume_details = fun_test.shared_variables["volume_details"]

        topology = fun_test.shared_variables["topology"]
        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        # Initializing fio_bs_iodepth variable as a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size

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

        # Setting the list of block size and IO depth combo
        fio_bs_iodepth = []
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        fio_bs_iodepth = benchmark_dict[testcase]['fio_bs_iodepth']
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, fio_bs_iodepth))

        fio_size = "16m"
        fio_timeout = 300
        fio_rwmixread = 25
        fio_modes = ['rw', ]

        # Setting expected FIO results
        expected_fio_result = {}
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))
        expected_fio_result = benchmark_dict[testcase]['expected_fio_result']
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, expected_fio_result))

        if len(fio_bs_iodepth) != len(expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        expected_volume_stats = benchmark_dict[testcase]['expected_volume_stats']
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, expected_volume_stats))

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write & read
        # only modes
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        for combo in fio_bs_iodepth:
            fio_result[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            fio_output[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            for mode in fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                fun_test.log("Running FIO {} test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats from all the 3 DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the 3 DUTs in dictionary format")
                initial_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    initial_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])

                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                           format(index))
                    initial_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the beginning of the test in DUT instance {}:".format(index))
                    fun_test.log(initial_volume_status[combo][mode][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, rwmixread=fio_rwmixread,
                                                         timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling the volume stats from all the three DUTs after the FIO test
                fun_test.log("Pulling the volume stats from all the 3 DUTs after the FIO test")
                final_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    final_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".
                                           format(index))
                    final_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the end of the test in DUT instance {}:".format(index))
                    fun_test.log(final_volume_status[combo][mode][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for index in range(len(dut_instance)):
                    diff_volume_stats[combo][mode][index] = {}
                    for key, value in final_volume_status[combo][mode][index].items():
                        if key in initial_volume_status[combo][mode][index]:
                            diff_volume_stats[combo][mode][index][key] = final_volume_status[combo][mode][index][key] -\
                                                                          initial_volume_status[combo][mode][index][key]
                    fun_test.log("Difference of volume status before and after the test in DUT instance {}:".
                                 format(index))
                    fun_test.log(diff_volume_stats[combo][mode][index])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        if actual < (value * (1 - pass_threshold)):
                            fio_result[combo][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + pass_threshold)):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for index in range(len(dut_instance)):
                    for key in expected_volume_stats[combo].keys():
                        deviation = int(tmp[0].strip('() ')) / 4
                        if key in diff_volume_stats[combo][mode][index]:
                            if key == "num_reads" and index != 2:
                                expected = expected_volume_stats[combo][key] / 2
                            else:
                                expected = expected_volume_stats[combo][key]
                            if diff_volume_stats[combo][mode][index][key] < (expected - deviation):
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is lesser than the expected value {} in DUT "
                                                  "instance {}".format(key,
                                                                       diff_volume_stats[combo][mode][index][key],
                                                                       expected, index))
                            elif diff_volume_stats[combo][mode][index][key] > (expected + deviation):
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is greater than the expected value {} in DUT "
                                                  "instance {}".format(key, diff_volume_stats[combo][mode][index][key],
                                                                       expected, index))
                            else:
                                fun_test.log("Final {} value {} is around the expected value {} within the expected "
                                             "deviation {} in DUT instance {}".
                                             format(key, diff_volume_stats[combo][mode][index][key], expected,
                                                    deviation, index))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in volume status".format(key))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in fio_bs_iodepth:
            for mode in fio_modes:
                fun_test.test_assert(fio_result[combo][mode], "FIO {} performance check for the block size & IO depth "
                                                              "combo {}".format(mode, combo))
                fun_test.test_assert(internal_result[combo][mode], "Volume stats check for the {} test for the block "
                                                                   "size & IO depth combo {}".format(mode, combo))


class FioRandReadWriteMix(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Random 75% Write & 25% Read performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__
        dut_instance = fun_test.shared_variables["dut_instance"]
        stat_uuids = fun_test.shared_variables["stat_uuids"]
        thin_uuids = fun_test.shared_variables["thin_uuids"]
        rds_uuids = fun_test.shared_variables["rds_uuids"]
        volume_details = fun_test.shared_variables["volume_details"]

        topology = fun_test.shared_variables["topology"]
        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        # Initializing fio_bs_iodepth variable as a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size

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

        # Setting the list of block size and IO depth combo
        fio_bs_iodepth = []
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        fio_bs_iodepth = benchmark_dict[testcase]['fio_bs_iodepth']
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, fio_bs_iodepth))

        fio_size = "16m"
        fio_timeout = 300
        fio_rwmixread = 25
        fio_modes = ['randrw', ]

        # Setting expected FIO results
        expected_fio_result = {}
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))
        expected_fio_result = benchmark_dict[testcase]['expected_fio_result']
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, expected_fio_result))

        if len(fio_bs_iodepth) != len(expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        expected_volume_stats = benchmark_dict[testcase]['expected_volume_stats']
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, expected_volume_stats))

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write & read
        # only modes
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        for combo in fio_bs_iodepth:
            fio_result[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            fio_output[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            for mode in fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                # Pulling the initial volume stats from all the 3 DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the 3 DUTs in dictionary format")
                initial_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    initial_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])

                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                           format(index))
                    initial_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the beginning of the test in DUT instance {}:".format(index))
                    fun_test.log(initial_volume_status[combo][mode][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, rwmixread=fio_rwmixread,
                                                         timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling the volume stats from all the three DUTs after the FIO test
                fun_test.log("Pulling the volume stats from all the 3 DUTs after the FIO test")
                final_volume_status[combo][mode] = {}
                for index, dut in enumerate(dut_instance):
                    final_volume_status[combo][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".
                                           format(index))
                    final_volume_status[combo][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the end of the test in DUT instance {}:".format(index))
                    fun_test.log(final_volume_status[combo][mode][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for index in range(len(dut_instance)):
                    diff_volume_stats[combo][mode][index] = {}
                    for key, value in final_volume_status[combo][mode][index].items():
                        if key in initial_volume_status[combo][mode][index]:
                            diff_volume_stats[combo][mode][index][key] = final_volume_status[combo][mode][index][key] -\
                                                                          initial_volume_status[combo][mode][index][key]
                    fun_test.log("Difference of volume status before and after the test in DUT instance {}:".
                                 format(index))
                    fun_test.log(diff_volume_stats[combo][mode][index])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        if actual < (value * (1 - pass_threshold)):
                            fio_result[combo][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + pass_threshold)):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for index in range(len(dut_instance)):
                    for key in expected_volume_stats[combo].keys():
                        deviation = int(tmp[0].strip('() ')) / 4
                        if key in diff_volume_stats[combo][mode][index]:
                            if key == "num_reads" and index != 2:
                                expected = expected_volume_stats[combo][key] / 2
                            else:
                                expected = expected_volume_stats[combo][key]
                            if diff_volume_stats[combo][mode][index][key] < (expected - deviation):
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is lesser than the expected value {} in DUT "
                                                  "instance {}".format(key, diff_volume_stats[combo][mode][index][key],
                                                                       expected, index))
                            elif diff_volume_stats[combo][mode][index][key] > (expected + deviation):
                                internal_result[combo][mode] = False
                                fun_test.critical("Final {} value {} is greater than the expected value {} in DUT "
                                                  "instance".format(key, diff_volume_stats[combo][mode][index][key],
                                                                    expected, index))
                            else:
                                fun_test.log("Final {} value {} is around the expected value {} within the expected "
                                             "deviation {} in DUT instance {}".
                                             format(key, diff_volume_stats[combo][mode][index][key], expected,
                                                    deviation, index))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in volume status".format(key))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in fio_bs_iodepth:
            for mode in fio_modes:
                fun_test.test_assert(fio_result[combo][mode], "FIO {} performance check for the block size & IO depth "
                                                              "combo {}".format(mode, combo))
                fun_test.test_assert(internal_result[combo][mode], "Volume stats check for the {} test for the block "
                                                                   "size & IO depth combo {}".format(mode, combo))


class FioLargeWriteReadOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Write & Read only performance(for both Sequential and random) for large sizes "
                                      "of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO write and read only test(without verify) for various sizes from the external Linux server and 
        check the performance are inline with the expected threshold.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__
        dut_instance = fun_test.shared_variables["dut_instance"]
        stat_uuids = fun_test.shared_variables["stat_uuids"]
        thin_uuids = fun_test.shared_variables["thin_uuids"]
        rds_uuids = fun_test.shared_variables["rds_uuids"]
        volume_details = fun_test.shared_variables["volume_details"]

        topology = fun_test.shared_variables["topology"]
        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance[-1].data_plane_ip

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        # Initializing fio_bs_iodepth variable as a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size

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

        # Setting the list of block size and IO depth combo
        fio_bs_iodepth = []
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        fio_bs_iodepth = benchmark_dict[testcase]['fio_bs_iodepth']
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, fio_bs_iodepth))

        # Setting the list of sizes to run the test
        fio_sizes = []
        if 'fio_size' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_size']:
            benchmark_parsing = False
            fun_test.critical("List of various sizes needed for this {} testcase is not available in the {} file"
                              .format(testcase, benchmark_file))
        fio_sizes = benchmark_dict[testcase]['fio_size']
        fun_test.log("List of various sizes going to be used for this {} testcase: {}".format(testcase, fio_sizes))

        # Setting expected FIO results
        expected_fio_result = {}
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))
        expected_fio_result = benchmark_dict[testcase]['expected_fio_result']
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, expected_fio_result))

        if len(fio_sizes) != len(expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))
        expected_volume_stats = benchmark_dict[testcase]['expected_volume_stats']
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, expected_volume_stats))

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        fio_timeout = 600
        fio_modes = ['read', 'randread', 'write', 'randwrite']
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes for all the sizes listed in fio_sizes variable
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        for size in fio_sizes:

            # The below check needs to be removed once the bugs #324 get resolved
            if size == "512m" or size == "896m":
                continue
            fio_result[size] = {}
            internal_result[size] = {}
            initial_volume_status[size] = {}
            fio_output[size] = {}
            final_volume_status[size] = {}
            diff_volume_stats[size] = {}
            for mode in fio_modes:

                # The below check needs to be removed once the bugs #299 get resolved
                if (size == "256m") and (mode == "write" or mode == "randwrite"):
                    continue
                tmp = fio_bs_iodepth.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[size][mode] = True
                internal_result[size][mode] = True

                fun_test.log("Running FIO {} only test for the size {} with the block size & IO depth set to {} & {}"
                             .format(mode, size, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats from all the 3 DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the 3 DUTs in dictionary format")
                initial_volume_status[size][mode] = {}
                for index, dut in enumerate(dut_instance):
                    initial_volume_status[size][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])

                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                           format(index))
                    initial_volume_status[size][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the beginning of the test in DUT instance {}:".format(index))
                    fun_test.log(initial_volume_status[size][mode][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[size][mode] = {}
                fio_output[size][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                        size=size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[size][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling the volume stats from all the three DUTs after the FIO test
                fun_test.log("Pulling the volume stats from all the 3 DUTs after the FIO test")
                final_volume_status[size][mode] = {}
                for index, dut in enumerate(dut_instance):
                    final_volume_status[size][mode][index] = {}
                    storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details[index]["type"],
                                                      stat_uuids[index])
                    command_result = {}
                    command_result = storage_controller.peek(props_tree)
                    fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".
                                           format(index))
                    final_volume_status[size][mode][index] = command_result["data"]
                    fun_test.log("Volume Status at the end of the test in DUT instance {}:".format(index))
                    fun_test.log(final_volume_status[size][mode][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[size][mode] = {}
                for index in range(len(dut_instance)):
                    diff_volume_stats[size][mode][index] = {}
                    for key, value in final_volume_status[size][mode][index].items():
                        if key in initial_volume_status[size][mode][index]:
                            diff_volume_stats[size][mode][index][key] = final_volume_status[size][mode][index][key] - \
                                                                        initial_volume_status[size][mode][index][key]
                    fun_test.log("Difference of volume status before and after the test in DUT instance {}:".
                                 format(index))
                    fun_test.log(diff_volume_stats[size][mode][index])

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in expected_fio_result[size][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[size][mode][op][field]
                        if actual < (value * (1 - pass_threshold)):
                            fio_result[size][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + pass_threshold)):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for index in range(len(dut_instance)):
                    for key in expected_volume_stats[size][mode].keys():
                        if key in diff_volume_stats[size][mode][index]:
                            expected = expected_volume_stats[size][mode][key]
                            if diff_volume_stats[size][mode][index][key] != expected:
                                internal_result[size][mode] = False
                                fun_test.critical("Final {} value {} is not equal to the expected value {} in DUT "
                                                  "instance {}".format(key, diff_volume_stats[size][mode][index][key],
                                                                       expected, index))
                            else:
                                fun_test.log("Final {} value {} is equal to the expected value {} in DUT instance {}".
                                             format(key, diff_volume_stats[size][mode][index][key], expected, index))
                        else:
                            internal_result[size][mode] = False
                            fun_test.critical("{} is not found in volume status".format(key))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for size in fio_sizes:
            # The below check needs to be removed once the bugs #324 get resolved
            if size == "512m" or size == "896m":
                continue
            for mode in fio_modes:
                # The below check needs to be removed once the bugs #299 get resolved
                if (size == "256m") and (mode == "write" or mode == "randwrite"):
                    continue
                fun_test.test_assert(fio_result[size][mode], "FIO {} {} performance check for the block size & IO "
                                                             "depth set to {} & {}".format(size, mode, fio_block_size,
                                                                                           fio_iodepth))
                fun_test.test_assert(internal_result[size][mode], "Volume stats check for the {} {} test for the block "
                                                                  "size & IO depth set to {} & {}".
                                     format(size, mode, fio_block_size, fio_iodepth))


if __name__ == "__main__":

    myscript = MyScript()
    myscript.add_test_case(FioSeqWriteSeqReadOnly)
    myscript.add_test_case(FioRandWriteRandReadOnly)
    myscript.add_test_case(FioSeqReadWriteMix)
    myscript.add_test_case(FioRandReadWriteMix)
    myscript.add_test_case(FioLargeWriteReadOnly())
    myscript.run()
