from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from lib.fun.f1 import F1
import uuid

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": Dut.DutInterface.INTERFACE_TYPE_PCIE
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
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        # Initializing volume related configs
        volume_details = {"ns_id": 1, "type": "VOL_TYPE_BLK_LOCAL_THIN", "capacity": 1073741824, "block_size": 4096,
                          "name": "thin-block1"}

        # Configuring Local thin block volume
        storage_controller = StorageController(target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)

        command_result = {}
        command_result = storage_controller.command("enable_counters")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on Dut Instance {}".format(0))

        command_result = {}
        command_result = storage_controller.ip_cfg(ip=dut_instance.data_plane_ip)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg {} on Dut Instance {}".
                             format(dut_instance.data_plane_ip, 0))

        command_result = {}
        thin_uuid = str(uuid.uuid4()).replace("-", "")[:10]
        command_result = storage_controller.create_thin_block_volume(capacity=volume_details["capacity"],
                                                                     block_size=volume_details["block_size"],
                                                                     name=volume_details["name"], uuid=thin_uuid)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "create_thin_block_volume on Dut Instance {}".format(0))

        command_result = {}
        command_result = storage_controller.attach_volume(ns_id=volume_details["ns_id"], uuid=thin_uuid,
                                                          remote_ip=linux_host.internal_ip)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Attaching thin local block volume on Dut Instance {}".format(0))

        fun_test.shared_variables["volume_details"] = volume_details
        fun_test.shared_variables["storage_controller"] = storage_controller
        fun_test.shared_variables["thin_uuid"] = thin_uuid

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class FioSeqWriteSeqReadOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of Thin Provisioned local block volume "
                                      "over RDS",
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        volume_details = fun_test.shared_variables["volume_details"]
        storage_controller = fun_test.shared_variables["storage_controller"]
        thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Start of benchmarking json file parsing and initializing various varaibles to run this testcase
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
        fio_timeout = 120
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

        # expected_fio_result = {
        #    (4, 32): {'write': {'write': {'bw': 646, 'iops': 161}},
        #              'read': {'read': {'bw': 726, 'iops': 181}}},
        #    (8, 16): {'write': {'write': {'bw': 1066, 'iops': 133}},
        #              'read': {'read': {'bw': 1236, 'iops': 154}}},
        #    (16, 16): {'write': {'write': {'bw': 1419, 'iops': 88}},
        #               'read': {'read': {'bw': 1793, 'iops': 111}}},
        #    (32, 64): {'write': {'write': {'bw': 1593, 'iops': 49}},
        #               'read': {'read': {'bw': 2143, 'iops': 66}}}
        # }

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

        # expected_volume_stats = {'write': {'fault_injection': 0, 'num_reads': 0, 'num_writes': 4096},
        #                         'read': {'fault_injection': 0, 'num_reads': 4096, 'num_writes': 0}}

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details["type"], thin_uuid)

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
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

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}

                command_result = storage_controller.peek(props_tree)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(dest_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = storage_controller.peek(props_tree)
                fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for key, value in final_volume_status[combo][mode].items():
                    if key in initial_volume_status[combo][mode]:
                        diff_volume_stats[combo][mode][key] = final_volume_status[combo][mode][key] - \
                                                              initial_volume_status[combo][mode][key]
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

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
                for key in expected_volume_stats[mode].keys():
                    if key in diff_volume_stats[combo][mode]:
                        if diff_volume_stats[combo][mode][key] != expected_volume_stats[mode][key]:
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[mode][key]))
                        else:
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(key, diff_volume_stats[combo][mode][key],
                                                expected_volume_stats[mode][key]))
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


class FioRandWriteRandReadOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary='Random Write & Read only performance of Thin Provisioned local block volume over'
                                      ' RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        volume_details = fun_test.shared_variables["volume_details"]
        storage_controller = fun_test.shared_variables["storage_controller"]
        thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Start of benchmarking json file parsing and initializing various varaibles to run this testcase
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
        fio_timeout = 120
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

        # expected_fio_result = {
        #    (4, 32): {'randwrite': {'write': {'bw': 616, 'iops': 152}},
        #              'randread': {'read': {'bw': 677, 'iops': 169}}},
        #    (8, 8): {'randwrite': {'write': {'bw': 979, 'iops': 122}},
        #             'randread': {'read': {'bw': 1088, 'iops': 136}}},
        #    (16, 16): {'randwrite': {'write': {'bw': 1327, 'iops': 83}},
        #               'randread': {'read': {'bw': 1544, 'iops': 96}}},
        #    (32, 16): {'randwrite': {'write': {'bw': 1538, 'iops': 47}},
        #               'randread': {'read': {'bw': 1891, 'iops': 59}}}
        # }

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

        # expected_volume_stats = {'randwrite': {'fault_injection': 0, 'num_reads': 0, 'num_writes': 4096},
        #                         'randread': {'fault_injection': 0, 'num_reads': 4096, 'num_writes': 0}}

        if 'pass_threshold' not in benchmark_dict[testcase]:
            pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(pass_threshold, testcase, benchmark_file))
        pass_threshold = benchmark_dict[testcase]['pass_threshold']

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        # End of benchmarking json file parsing

        fio_result = {}
        internal_result = {}

        props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details["type"], thin_uuid)

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

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}

                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(dest_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for key, value in final_volume_status[combo][mode].items():
                    if key in initial_volume_status[combo][mode]:
                        diff_volume_stats[combo][mode][key] = final_volume_status[combo][mode][key] - \
                                                              initial_volume_status[combo][mode][key]
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

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
                for key in expected_volume_stats[mode].keys():
                    if key in diff_volume_stats[combo][mode]:
                        if diff_volume_stats[combo][mode][key] != expected_volume_stats[mode][key]:
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[mode][key]))
                        else:
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(key, diff_volume_stats[combo][mode][key],
                                                expected_volume_stats[mode][key]))
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


class FioSeqReadWriteMix(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary='Sequential 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        volume_details = fun_test.shared_variables["volume_details"]
        storage_controller = fun_test.shared_variables["storage_controller"]
        thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Start of benchmarking json file parsing and initializing various varaibles to run this testcase
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
        fio_rwmixread = 25
        fio_timeout = 120
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

        props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details["type"], thin_uuid)

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

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}

                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(dest_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, rwmixread=fio_rwmixread,
                                                         timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for key, value in final_volume_status[combo][mode].items():
                    if key in initial_volume_status[combo][mode]:
                        diff_volume_stats[combo][mode][key] = final_volume_status[combo][mode][key] - \
                                                              initial_volume_status[combo][mode][key]
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

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
                for key in expected_volume_stats[combo].keys():
                    deviation = int(tmp[0].strip('() ')) / 4
                    if key in diff_volume_stats[combo][mode]:
                        if diff_volume_stats[combo][mode][key] < (expected_volume_stats[combo][key] - deviation):
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is lesser than the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[combo][key]))
                        elif diff_volume_stats[combo][mode][key] > (expected_volume_stats[combo][key] + deviation):
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is greater than the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[combo][key]))
                        else:
                            fun_test.log("Final {} value {} is around the expected value {} within the expected "
                                         "deviation {}".format(key, diff_volume_stats[combo][mode][key],
                                                               expected_volume_stats[combo][key], deviation))
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
                              summary='Random 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        volume_details = fun_test.shared_variables["volume_details"]
        storage_controller = fun_test.shared_variables["storage_controller"]
        thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Start of benchmarking json file parsing and initializing various varaibles to run this testcase
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
        fio_rwmixread = 25
        fio_timeout = 120
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

        props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details["type"], thin_uuid)

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

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}

                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(dest_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         size=fio_size, iodepth=fio_iodepth, rwmixread=fio_rwmixread,
                                                         timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = storage_controller.peek(props_tree)
                # fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for key, value in final_volume_status[combo][mode].items():
                    if key in initial_volume_status[combo][mode]:
                        diff_volume_stats[combo][mode][key] = final_volume_status[combo][mode][key] - \
                                                              initial_volume_status[combo][mode][key]
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

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
                for key in expected_volume_stats[combo].keys():
                    deviation = int(tmp[0].strip('() ')) / 4
                    if key in diff_volume_stats[combo][mode]:
                        if diff_volume_stats[combo][mode][key] < (expected_volume_stats[combo][key] - deviation):
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is lesser than the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[combo][key]))
                        elif diff_volume_stats[combo][mode][key] > (expected_volume_stats[combo][key] + deviation):
                            internal_result[combo][mode] = False
                            fun_test.critical("Final {} value {} is greater than the expected value {}".
                                              format(key, diff_volume_stats[combo][mode][key],
                                                     expected_volume_stats[combo][key]))
                        else:
                            fun_test.log("Final {} value {} is around the expected value {} within the expected "
                                         "deviation {}".format(key, diff_volume_stats[combo][mode][key],
                                                               expected_volume_stats[combo][key], deviation))
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
                              summary='Write & Read only performance(for both Sequential and random) for large sizes '
                                      'of Thin Provisioned local block volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO write and read only test(without verify) for various sizes from the external Linux server and 
        check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut_instance = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance.data_plane_ip

        volume_details = fun_test.shared_variables["volume_details"]
        storage_controller = fun_test.shared_variables["storage_controller"]
        thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Start of benchmarking json file parsing and initializing various varaibles to run this testcase
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

        fio_timeout = 360
        fio_modes = ['read', 'randread', 'write', 'randwrite']

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
            fun_test.critical("Mismatch in total number of sizes and its benchmarking results length")

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

        props_tree = "{}/{}/{}/{}".format("storage", "volumes", volume_details["type"], thin_uuid)

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
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

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[size][mode] = {}

                command_result = storage_controller.peek(props_tree)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[size][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[size][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[size][mode] = {}
                fio_output[size][mode] = linux_host.fio(dest_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                        size=size, iodepth=fio_iodepth, timeout=fio_timeout)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[size][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[size][mode] = {}
                command_result = storage_controller.peek(props_tree)
                fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[size][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[size][mode])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[size][mode] = {}
                for key, value in final_volume_status[size][mode].items():
                    if key in initial_volume_status[size][mode]:
                        diff_volume_stats[size][mode][key] = final_volume_status[size][mode][key] - \
                                                             initial_volume_status[size][mode][key]
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[size][mode])

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
                for key in expected_volume_stats[size][mode].keys():
                    if key in diff_volume_stats[size][mode]:
                        if diff_volume_stats[size][mode][key] != expected_volume_stats[size][mode][key]:
                            internal_result[size][mode] = False
                            fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                              format(key, diff_volume_stats[size][mode][key],
                                                     expected_volume_stats[size][mode][key]))
                        else:
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(key, diff_volume_stats[size][mode][key],
                                                expected_volume_stats[size][mode][key]))
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
    myscript.add_test_case(FioSeqWriteSeqReadOnly())
    # myscript.add_test_case(FioRandWriteRandReadOnly())
    # myscript.add_test_case(FioSeqReadWriteMix())
    # myscript.add_test_case(FioRandReadWriteMix())
    # myscript.add_test_case(FioLargeWriteReadOnly())
    myscript.run()
