from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from lib.fun.f1 import F1
import random

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


def fio_parser(arg1, **kwargs):
    arg1.remote_fio(**kwargs)
    arg1.disconnect()


class LsvCryptoVolumeScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut_instance = self.topology.get_dut_instance(index=0)
        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["ctrl_created"] = False

    def cleanup(self):
        self.storage_controller.disconnect()
        if self.topology:
            self.topology.cleanup()
        # pass


class LsvCryptoVolumeTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        benchmark_parsing = True
        testcase_file = ""
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))

        testcase_dict = {}
        testcase_dict = utils.parse_file_to_json(testcase_file)

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of block size and IO depth combo
        if 'fio_bs_iodepth' not in testcase_dict[testcase] or not testcase_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file.".format(testcase, testcase_file))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_lsv_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_lsv_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal LSV stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected lsv volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_lsv_stats))

        if ('expected_blt_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_blt_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal BLT stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected internal BLT stats for this {} testcase: \n{}".
                     format(testcase, self.expected_blt_stats))

        if hasattr(self, "compress") and self.compress:
            if ('expected_compression_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_compression_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected internal compression stats needed for this {} testcase is not available in "
                                  "the {} file".format(testcase, testcase_dict))
            if ('expected_uncompression_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_uncompression_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected internal uncompression stats needed for this {} testcase is not available "
                                  "in the {} file".format(testcase, testcase_dict))

        if hasattr(self, "encrypt") and self.encrypt:
            if ('expected_decryption_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_decryption_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected decryption stats for {} testcase is not available in the {} file".
                                  format(testcase, testcase_dict))
            if ('expected_encryption_stats' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['expected_encryption_stats']):
                benchmark_parsing = False
                fun_test.critical("Expected encryption stats for {} testcase is not available in the {} file".
                                  format(testcase, testcase_dict))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance = self.topology.get_dut_instance(index=0)
        self.linux_host = self.topology.get_tg_instance(tg_index=0)

        self.linux_host_inst = {}
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        key256_count = 0
        key384_count = 0
        key512_count = 0
        self.blt_capacity = 0
        self.blt_creation_fail = None

        if hasattr(self, "encrypt") and self.encrypt:
            # Getting initial crypto filter stats
            initial_filter_values = {}
            for filter_param in self.filter_params:
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = self.storage_controller.peek(crypto_props_tree)
                if command_result["data"] is None:
                    command_result["data"] = 0
                initial_filter_values[filter_param] = command_result["data"]

        # Configuring EC volume
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

        # Configuring controller
        if not fun_test.shared_variables["ctrl_created"]:
            command_result = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip,
                                                            command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT".
                                 format(self.dut_instance.data_plane_ip))
            fun_test.shared_variables["ctrl_created"] = True

        self.uuid = {}
        self.uuid["blt"] = []
        self.uuid["jvol"] = []
        self.uuid["lsv"] = []
        self.volume_list = []
        self.all_volume = []
        self.detach_count = 0

        # LSV should be 70% of BLT capacity. So increase the BLT capacity by 30% and use BLT capacity for LSV.
        # Only single BLT can be used with LSV
        self.blt_capacity = (self.blt_details["capacity"] * self.lsv_head / 100) + self.blt_details["capacity"]
        # Make sure the capacity is multiple of block size
        self.blt_capacity = ((self.blt_capacity + self.blt_details["block_size"] - 1) /
                             self.blt_details["block_size"]) * self.blt_details["block_size"]

        self.uuid["blt"] = utils.generate_uuid()
        command_result = self.storage_controller.create_volume(type=self.vol_types["blt"],
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_details["block_size"],
                                                               name="thin_block1",
                                                               uuid=self.uuid["blt"],
                                                               command_duration=self.command_timeout)
        if not command_result["status"]:
            self.blt_creation_fail = True
            fun_test.test_assert(command_result["status"], "BLT creation with uuid {} & capacity {}".
                                 format(self.uuid["blt"], self.blt_capacity))

        self.volume_list.append("blt")
        self.all_volume.append("blt")

        # Key generation for encryption based on size or input is random or alternate
        if self.key_size == "random":
            rand_key = random.choice(self.key_range)
            key_size = rand_key
            self.xts_key = utils.generate_key(rand_key)
            if rand_key == 32:
                key256_count += 1
            elif rand_key == 48:
                key384_count += 1
            else:
                key512_count += 1
        else:
            key_size = self.key_size
            self.xts_key = utils.generate_key(self.key_size)

        self.xts_tweak = utils.generate_key(self.xtweak_size)

        self.attach_type = "VOL_TYPE_BLK_LSV"
        # The minimum jvol_capacity requirement is LSV chunk size * lsv block size * 4
        self.jvol_capacity = \
            self.blt_details["block_size"] * self.jvol_details["multiplier"] * self.lsv_details["chunk_size"]
        self.uuid["jvol"] = utils.generate_uuid()
        command_result = self.storage_controller.create_volume(type=self.vol_types["jvol"],
                                                               capacity=self.jvol_capacity,
                                                               block_size=self.jvol_details["block_size"],
                                                               name="jvol1",
                                                               uuid=self.uuid["jvol"],
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "JVol creation with uuid {} & capacity {}".
                             format(self.uuid["jvol"], self.jvol_capacity))
        self.all_volume.append("jvol")
        self.all_volume.append("lsv")
        # Creating LSV and setting it to attach_uuid
        self.volume_list.append("lsv")
        self.uuid["lsv"] = utils.generate_uuid()
        self.attach_uuid = self.uuid["lsv"]
        self.lsv_capacity = self.blt_details["capacity"]
        self.lsv_blocksize = self.blt_details["block_size"]
        if hasattr(self, "compress") and self.compress:
            command_result = self.storage_controller.create_volume(type=self.vol_types["lsv"],
                                                                   capacity=self.lsv_capacity,
                                                                   block_size=self.lsv_blocksize,
                                                                   name="lsv1",
                                                                   uuid=self.attach_uuid,
                                                                   jvol_uuid=self.uuid["jvol"],
                                                                   pvol_id=[self.uuid["blt"]],
                                                                   group=1,
                                                                   encrypt=self.encrypt,
                                                                   key=self.xts_key,
                                                                   xtweak=self.xts_tweak,
                                                                   compress=self.compress,
                                                                   zip_filter=self.zip_filter,
                                                                   zip_effort=self.zip_effort,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "LSV creation with uuid {} & capacity {} with compression "
                                                           "using {} byte key".
                                 format(self.attach_uuid, self.lsv_capacity, key_size))
        else:
            command_result = self.storage_controller.create_volume(type=self.vol_types["lsv"],
                                                                   capacity=self.lsv_capacity,
                                                                   block_size=self.lsv_blocksize,
                                                                   name="lsv1",
                                                                   uuid=self.attach_uuid,
                                                                   jvol_uuid=self.uuid["jvol"],
                                                                   pvol_id=[self.uuid["blt"]],
                                                                   group=1,
                                                                   encrypt=self.encrypt,
                                                                   key=self.xts_key,
                                                                   xtweak=self.xts_tweak,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "LSV creation with uuid {} & capacity {} using {} byte key".
                                 format(self.attach_uuid, self.lsv_capacity, key_size))

        if hasattr(self, "traffic_parallel") and self.traffic_parallel:
            attach_count = 0
            for x in range(1, self.parallel_count + 1, 1):
                command_result = self.storage_controller.volume_attach_remote(
                    ns_id=x,
                    uuid=self.attach_uuid,
                    remote_ip=self.linux_host.internal_ip,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.simple_assert(command_result["status"], "LSV with uuid {} parallel attach {}".
                                       format(self.attach_uuid, x))
                attach_count += 1
            fun_test.test_assert_expected(self.parallel_count, attach_count,
                                          message="Parallel count & attach count")
        else:
            command_result = self.storage_controller.volume_attach_remote(ns_id=self.ns_id,
                                                                          uuid=self.attach_uuid,
                                                                          remote_ip=self.linux_host.internal_ip,
                                                                          command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attach LSV with uuid {}".format(self.attach_uuid))

        # Check the expected filter params
        if self.encrypt:
            final_filter_values = {}
            diff_filter_values = {}
            for filter_param in self.filter_params:
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = self.storage_controller.peek(crypto_props_tree)
                if command_result["data"] is None:
                    command_result["data"] = 0
                final_filter_values[filter_param] = command_result["data"]
                if self.traffic_parallel:
                    multiplier = self.parallel_count
                else:
                    multiplier = 1
                # Computing expected filter value
                if filter_param != "vol_decrypt_filter_added" and filter_param != "vol_encrypt_filter_added":
                    evalue = 2 * multiplier
                else:
                    evalue = multiplier
                diff_filter_values[filter_param] = \
                    final_filter_values[filter_param] - initial_filter_values[filter_param]
                fun_test.test_assert_expected(evalue, diff_filter_values[filter_param],
                                              message="Comparing crypto filter {} count".format(filter_param))

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_output = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}
        diff_vol_stats = {}
        diff_crypto_stats = {}
        initial_vol_stats = {}
        final_vol_stats = {}
        initial_zip_stats = {}
        final_zip_stats = {}
        diff_zip_stats = {}
        expected_stats = {}

        for combo in self.fio_bs_iodepth:
            fio_output[combo] = {}
            final_vol_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}
            diff_vol_stats[combo] = {}
            diff_crypto_stats[combo] = {}
            initial_vol_stats[combo] = {}
            initial_zip_stats[combo] = {}
            final_zip_stats[combo] = {}
            diff_zip_stats[combo] = {}

            if combo in self.expected_lsv_stats:
                expected_lsv_stats = self.expected_lsv_stats[combo]
            else:
                expected_lsv_stats = self.expected_lsv_stats

            if combo in self.expected_blt_stats:
                expected_blt_stats = self.expected_blt_stats[combo]
            else:
                expected_blt_stats = self.expected_blt_stats

            if hasattr(self, "compress") and self.compress:
                if combo in self.expected_compression_stats:
                    expected_compression_stats = self.expected_compression_stats[combo]
                else:
                    expected_compression_stats = self.expected_compression_stats

                if combo in self.expected_uncompression_stats:
                    expected_uncompression_stats = self.expected_uncompression_stats[combo]
                else:
                    expected_uncompression_stats = self.expected_uncompression_stats

            if hasattr(self, "encrypt") and self.encrypt:
                if combo in self.expected_decryption_stats:
                    expected_decryption_stats = self.expected_decryption_stats[combo]
                else:
                    expected_decryption_stats = self.expected_decryption_stats

                if combo in self.expected_encryption_stats:
                    expected_encryption_stats = self.expected_encryption_stats[combo]
                else:
                    expected_encryption_stats = self.expected_encryption_stats

            for mode in self.fio_modes:
                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                for loop in range(0, self.fio_loop, 1):
                    fun_test.log("Running loop {} of {}".format((loop+1), self.fio_loop))
                    initial_vol_stats[combo][mode] = {}
                    for vol_type in self.volume_list:
                        initial_vol_stats[combo][mode][vol_type] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                     "volumes",
                                                                     self.vol_types[vol_type],
                                                                     self.uuid[vol_type],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT".format(vol_type))
                        initial_vol_stats[combo][mode][vol_type] = command_result["data"]
                        fun_test.log("{} stats at the beginning of the test:".format(vol_type))
                        fun_test.log(initial_vol_stats[combo][mode][vol_type])

                    # Use this check as without encrypt flag the stats are not enabled.
                    if hasattr(self, "encrypt") and self.encrypt:
                        initial_crypto_stats[combo][mode] = {}
                        self.crypto_ops = ["encryption", "decryption"]
                        for x in self.crypto_ops:
                            initial_crypto_stats[combo][mode][x] = {}
                            crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                        self.attach_type,
                                                                        self.attach_uuid, x)

                            command_result = self.storage_controller.peek(crypto_props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats for LSV".
                                                   format(x))
                            if command_result["data"] is None:
                                command_result["data"] = 0
                            initial_crypto_stats[combo][mode][x] = command_result["data"]

                            fun_test.log("LSV : {} stats at the beginning of the test: {}".
                                         format(x, initial_crypto_stats[combo][mode][x]))

                    # Use this check as without compress flag the stats are not enabled.
                    if hasattr(self, "compress") and self.compress:
                        initial_zip_stats[combo][mode] = {}
                        self.zip_ops = ["compression", "uncompression"]
                        for x in self.zip_ops:
                            initial_zip_stats[combo][mode][x] = {}
                            zip_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     self.attach_type,
                                                                     self.attach_uuid, x)
                            command_result = self.storage_controller.peek(zip_props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats on LSV".format(x))
                            initial_zip_stats[combo][mode][x] = command_result["data"]
                            if initial_zip_stats[combo][mode][x] is None:
                                initial_zip_stats[combo][mode][x] = 0
                            fun_test.log("LSV : {} stats at the beginning of the test:".format(x))
                            fun_test.log(initial_zip_stats[combo][mode][x])

                    if not self.traffic_parallel:
                        if mode == "rw" or mode == "randrw":
                            fio_output[combo][mode] = {}
                            fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                 rw=mode,
                                                                                 bs=fio_block_size,
                                                                                 iodepth=fio_iodepth,
                                                                                 rwmixread=self.fio_rwmixread,
                                                                                 nsid=self.ns_id,
                                                                                 **self.fio_cmd_args)
                        else:
                            fio_output[combo][mode] = {}
                            fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                 rw=mode,
                                                                                 bs=fio_block_size,
                                                                                 iodepth=fio_iodepth,
                                                                                 nsid=self.ns_id,
                                                                                 **self.fio_cmd_args)
                        fun_test.test_assert(fio_output[combo][mode], "Fio test completed for {} mode & {} combo".
                                             format(mode, combo))
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fio_output[combo][mode])
                        self.linux_host.disconnect()
                    else:
                        fun_test.log("Running fio test is threaded mode...")
                        thread_id = {}
                        wait_time = 0
                        self.attach_count = self.parallel_count + 1
                        for x in range(1, self.attach_count, 1):
                            if mode == "rw" or mode == "randrw":
                                wait_time = self.attach_count - x
                                fio_output[combo][mode] = {}
                                self.linux_host_inst[x] = self.linux_host.clone()
                                thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                             func=fio_parser,
                                                                             arg1=self.linux_host_inst[x],
                                                                             destination_ip=destination_ip,
                                                                             rw=mode,
                                                                             rwmixread=self.fio_rwmixread,
                                                                             bs=fio_block_size,
                                                                             iodepth=fio_iodepth,
                                                                             nsid=x,
                                                                             **self.fio_cmd_args)
                            else:
                                wait_time = self.attach_count - x
                                fio_output[combo][mode] = {}
                                self.linux_host_inst[x] = self.linux_host.clone()
                                thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                             func=fio_parser,
                                                                             arg1=self.linux_host_inst[x],
                                                                             destination_ip=destination_ip,
                                                                             rw=mode,
                                                                             bs=fio_block_size,
                                                                             iodepth=fio_iodepth,
                                                                             nsid=x,
                                                                             **self.fio_cmd_args)
                            fun_test.sleep("Fio Threadzz", seconds=1)

                        fun_test.sleep("Sleeping between thread join...", seconds=10)
                        for x in range(1, self.attach_count, 1):
                            fun_test.log("Joining thread {}".format(x))
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])

                        if self.linux_host.command("pgrep fio"):
                            timer_kill = FunTimer(max_time=self.fio_cmd_args["timeout"])
                            while not timer_kill.is_expired():
                                if not self.linux_host.command("pgrep fio"):
                                    break
                                else:
                                    fun_test.sleep("Waiting for fio to exit...", seconds=10)

                            fun_test.log("Timer expired, killing fio...")
                            self.linux_host.command("for i in `pgrep fio`;do kill -9 $i;done")

                            fun_test.log(command_result)
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

                    final_vol_stats[combo][mode] = {}
                    for vol_type in self.volume_list:
                        final_vol_stats[combo][mode][vol_type] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                     "volumes",
                                                                     self.vol_types[vol_type],
                                                                     self.uuid[vol_type],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Final {} stats of DUT".format(vol_type))
                        final_vol_stats[combo][mode][vol_type] = command_result["data"]
                        fun_test.log("{} stats at the end of the test:".format(vol_type))
                        fun_test.log(final_vol_stats[combo][mode][vol_type])

                    diff_vol_stats[combo][mode] = {}
                    for vol_type in self.volume_list:
                        diff_vol_stats[combo][mode][vol_type] = {}
                        for fkey, fvalue in final_vol_stats[combo][mode][vol_type].items():
                            if fkey not in expected_lsv_stats[mode] or fkey == "fault_injection":
                                diff_vol_stats[combo][mode][vol_type][fkey] = fvalue
                                continue
                            if fkey in initial_vol_stats[combo][mode][vol_type]:
                                ivalue = initial_vol_stats[combo][mode][vol_type][fkey]
                                diff_vol_stats[combo][mode][vol_type][fkey] = fvalue - ivalue
                            else:
                                fun_test.simple_assert(False,
                                                       message="{} key not found in vol_type {} initial stat {}".
                                                       format(fkey,
                                                              vol_type, initial_vol_stats[combo][mode][vol_type]))
                        fun_test.log("Difference of {} stats before and after the test:".format(vol_type))
                        fun_test.log(diff_vol_stats[combo][mode][vol_type])

                    # Checking if the numbers match the expected value
                    total_diff_stats = 0
                    for vol_type in self.volume_list:
                        if vol_type == "blt":
                            expected_stats[mode] = expected_blt_stats[mode]
                            threshold_check = self.blt_pass_threshold
                        elif vol_type == "lsv":
                                expected_stats[mode] = expected_lsv_stats[mode]
                                threshold_check = self.lsv_pass_threshold

                        for ekey, evalue in expected_stats[mode].items():
                            actual = diff_vol_stats[combo][mode][vol_type][ekey]
                            if actual != evalue:
                                if (actual < evalue) and ((evalue - actual) <= threshold_check):
                                    fun_test.add_checkpoint(
                                        "{} check for {} for {} test for the block size & IO "
                                        "depth combo {}".
                                        format(ekey, vol_type, mode, combo), "PASSED", evalue, actual)
                                    fun_test.critical(
                                        "Final {} value {} for {} is within the expected "
                                        "range {} for combo {} & mode {}".format(ekey, actual, vol_type, evalue,
                                                                                 combo, mode))
                                elif (actual > evalue) and ((actual - evalue) <= threshold_check):
                                    fun_test.add_checkpoint(
                                        "{} check for {} for {} test for the block size & IO "
                                        "depth combo {}".
                                        format(ekey, vol_type, mode, combo), "PASSED", evalue, actual)
                                    fun_test.critical(
                                        "Final {} value {} for {} is within the expected "
                                        "range {}".format(ekey, actual, vol_type, evalue))
                                else:
                                    fun_test.simple_assert(False,
                                                           message="Final {} value {} for {} is not within the "
                                                                   "expected range {} for combo {} & mode {}".
                                                           format(ekey, actual, vol_type, evalue, combo, mode))
                            else:
                                fun_test.add_checkpoint(
                                    "{} check for {} for {} test for the block size & IO "
                                    "depth combo {}".
                                    format(ekey, vol_type, mode, combo), "PASSED", evalue, actual)
                                fun_test.log(
                                    "Final {} value {} for {} matches the expected "
                                    "value {}".format(ekey, actual, vol_type, evalue))
                            if ekey == "num_reads" or ekey == "num_writes":
                                if vol_type == "lsv":
                                    total_diff_stats += diff_vol_stats[combo][mode][vol_type][ekey]

                    if hasattr(self, "encrypt") and self.encrypt:
                        final_crypto_stats[combo][mode] = {}
                        diff_crypto_stats[combo][mode] = {}
                        for x in self.crypto_ops:
                            diff_crypto_stats[combo][mode][x] = {}
                            final_crypto_stats[combo][mode][x] = {}
                            crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                        self.attach_type,
                                                                        self.attach_uuid, x)

                            command_result = self.storage_controller.peek(crypto_props_tree)
                            fun_test.simple_assert(command_result["status"], "Final {} stats for LSV".
                                                   format(x))
                            final_crypto_stats[combo][mode][x] = command_result["data"]
                            fun_test.log("LSV : {} stats at the end of the test: {}".
                                         format(x, final_crypto_stats[combo][mode][x]))

                            if x == "encryption":
                                expected_crypto_stats = expected_encryption_stats[mode]
                            elif x == "decryption":
                                expected_crypto_stats = expected_decryption_stats[mode]

                            for fkey, fvalue in final_crypto_stats[combo][mode][x].items():
                                if fkey not in expected_crypto_stats:
                                    diff_crypto_stats[combo][mode][x][fkey] = fvalue
                                    continue
                                if fkey in initial_crypto_stats[combo][mode][x]:
                                    ivalue = initial_crypto_stats[combo][mode][x][fkey]
                                    diff_crypto_stats[combo][mode][x][fkey] = fvalue - ivalue
                                else:
                                    fun_test.simple_assert(False,
                                                           message="{} key not found in initial stat {}".
                                                           format(fkey, initial_crypto_stats[combo][mode][x]))
                            fun_test.log("Difference of LSV {} stats before and after the test: {}".
                                         format(x, diff_crypto_stats[combo][mode][x]))

                            for ekey, evalue in expected_crypto_stats.items():
                                if ekey in diff_crypto_stats[combo][mode][x]:
                                    actual = diff_crypto_stats[combo][mode][x][ekey]
                                    fun_test.test_assert_expected(evalue, actual,
                                                                  message="{} : {} stats for {} mode & {} combo on "
                                                                          "LSV".format(x, ekey, mode, combo))
                                else:
                                    fun_test.simple_assert(False,
                                                           message="{} key not found in diff stat {}".
                                                           format(ekey, diff_crypto_stats[combo][mode][x]))
                        if hasattr(self, "crypto_ops_params"):
                            filter_values = []
                            for i in self.crypto_ops_params:
                                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", i)
                                command_result = self.storage_controller.peek(crypto_props_tree)
                                filter_values.append(command_result["data"])

                            fun_test.test_assert(expression=len(set(filter_values)) == 1,
                                                 message="All filter counter stats {} match".format(filter_values))

                    if hasattr(self, "compress") and self.compress:
                        final_zip_stats[combo][mode] = {}
                        diff_zip_stats[combo][mode] = {}
                        for x in self.zip_ops:

                            final_zip_stats[combo][mode][x] = {}
                            diff_zip_stats[combo][mode][x] = {}
                            zip_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     self.attach_type,
                                                                     self.attach_uuid, x)
                            command_result = self.storage_controller.peek(zip_props_tree)
                            fun_test.simple_assert(command_result["status"], "Final {} stats on LSV".format(x))
                            final_zip_stats[combo][mode][x] = command_result["data"]
                            if final_zip_stats[combo][mode][x] is None:
                                final_zip_stats[combo][mode][x] = 0
                            fun_test.log("LSV {} stats at the end of the test:".format(x))
                            fun_test.log(final_zip_stats[combo][mode][x])

                            if x == "compression":
                                expected_zip_stats = expected_compression_stats[mode]
                            elif x == "uncompression":
                                expected_zip_stats = expected_uncompression_stats[mode]

                            for fkey, fvalue in final_zip_stats[combo][mode][x].items():
                                if fkey not in expected_zip_stats:
                                    diff_zip_stats[combo][mode][x][fkey] = fvalue
                                    continue
                                if fkey in initial_zip_stats[combo][mode][x]:
                                    ivalue = initial_zip_stats[combo][mode][x][fkey]
                                    diff_zip_stats[combo][mode][x][fkey] = fvalue - ivalue
                                else:
                                    fun_test.simple_assert(False,
                                                           message="{} key not found in initial stat {}".
                                                           format(fkey, initial_zip_stats[combo][mode][x]))
                            fun_test.log("Difference of LSV {} stats before and after the test: {}".
                                         format(x, diff_zip_stats[combo][mode][x]))

                            for ekey, evalue in expected_zip_stats.items():
                                if ekey in diff_zip_stats[combo][mode][x]:
                                    actual = diff_zip_stats[combo][mode][x][ekey]
                                    fun_test.test_assert_expected(evalue, actual,
                                                                  message="{} : {} stats for {} mode & {} combo on "
                                                                          "LSV".format(x, ekey, mode, combo))
                                else:
                                    fun_test.simple_assert(False,
                                                           message="{} key not found in diff stat {}".
                                                           format(ekey, diff_zip_stats[combo][mode][x]))

    def cleanup(self):
        if hasattr(self, "host_disconnect") and self.host_disconnect:
            self.linux_host.disconnect()

        if not self.blt_creation_fail:
            if self.traffic_parallel:
                for x in range(1, self.parallel_count + 1, 1):
                    command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                                  uuid=self.attach_uuid,
                                                                                  remote_ip=self.linux_host.internal_ip)
                    fun_test.log(command_result)
                    fun_test.simple_assert(command_result["status"], "Detach vol {} with uuid {}".
                                           format(x, self.attach_uuid))
                    self.detach_count += 1

                fun_test.test_assert_expected(self.parallel_count, self.detach_count,
                                              message="Parallel count & detach count")

            else:
                command_result = self.storage_controller.volume_detach_remote(ns_id=self.ns_id,
                                                                              uuid=self.attach_uuid,
                                                                              remote_ip=self.linux_host.internal_ip)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Detach vol with uuid {}".format(self.attach_uuid))

            command_result = self.storage_controller.delete_volume(capacity=self.lsv_capacity,
                                                                   block_size=self.lsv_blocksize,
                                                                   name="lsv1",
                                                                   uuid=self.attach_uuid,
                                                                   type=self.attach_type)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleted LSV")
            command_result = self.storage_controller.delete_volume(capacity=self.jvol_capacity,
                                                                   block_size=self.jvol_details["block_size"],
                                                                   name="jvol1",
                                                                   uuid=self.uuid["jvol"],
                                                                   type=self.vol_types["jvol"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleted Journal")
            command_result = self.storage_controller.delete_volume(capacity=self.blt_capacity,
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block1",
                                                                   uuid=self.uuid["blt"],
                                                                   type=self.vol_types["blt"])
            fun_test.test_assert(command_result["status"], "Deleting BLT with uuid {} on DUT".format(self.uuid["blt"]))

        # Verify cleanup is successful
        for vol_type in self.all_volume:
            if vol_type == "blt":
                storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                          self.vol_types[vol_type], self.uuid[vol_type])
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(expression=command_result["data"] is None,
                                       message="BLT with uuid {} removal".format(self.uuid[vol_type]))
            else:
                storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                          self.vol_types[vol_type], self.uuid[vol_type])
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(expression=command_result["data"] is None,
                                       message="{} with uuid {} removal".format(vol_type, self.uuid[vol_type]))


class LsvKey256(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="LSV with 256 bit key and run FIO with different RW pattern(write,read,"
                                      "randwrite,randread), with different block size & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey256RW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="LSV with 256 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey256RandRW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="LSV with 256 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey256RandRW50(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="LSV with 256 bit key and run FIO RandRW(50%RW) pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey512(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="LSV with 512 bit key and run FIO with different RW pattern(write,read,"
                                      "randwrite,randread), with different block size & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey512RW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="LSV with 512 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey512RandRW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="LSV with 512 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvKey512RandRW50(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="LSV with 512 bit key and run FIO RandRW(50%RW) pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvEncCompress(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="LSV with random key & compression and run diff FIO RW pattern(write,"
                                      "read,randwrite,randread) with different block size & depth & deadbeef data "
                                      "pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvEncCompressRW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="LSV with random key & compression and run FIO RW pattern set to"
                                      " rwmix:30 using different block size & depth & deadbeef data pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvEncCompressRandRW(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="LSV with random key & compression and run FIO RandRW pattern"
                                      " with different block size & depth & deadbeef data pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class LsvEncDeadBeef(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="LSV with random key and run diff FIO RW pattern(write,"
                                      "randwrite), with different block size & depth & deadbeef "
                                      "pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel.
        ''')


class LsvEncZeroPattern(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=13,
                              summary="LSV with random key and run diff FIO RW pattern(write,"
                                      "randwrite), with different block size & depth & 0x000000000 string "
                                      "pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel.
        ''')


class LsvEncZeroHPattern(LsvCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=14,
                              summary="LSV with random key and run diff FIO RW pattern(write,read,"
                                      "randwrite,randread), with different block size & depth & 0x000000000 hex "
                                      "pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel.
        ''')


if __name__ == "__main__":
    lsvscript = LsvCryptoVolumeScript()
    lsvscript.add_test_case(LsvKey256())
    lsvscript.add_test_case(LsvKey256RW())
    lsvscript.add_test_case(LsvKey256RandRW())
    lsvscript.add_test_case(LsvKey256RandRW50())
    lsvscript.add_test_case(LsvKey512())
    lsvscript.add_test_case(LsvKey512RW())
    lsvscript.add_test_case(LsvKey512RandRW())
    lsvscript.add_test_case(LsvKey512RandRW50())
    lsvscript.add_test_case(LsvEncCompress())
    lsvscript.add_test_case(LsvEncCompressRW())
    lsvscript.add_test_case(LsvEncCompressRandRW())
    lsvscript.add_test_case(LsvEncDeadBeef())
    lsvscript.add_test_case(LsvEncZeroPattern())
    lsvscript.add_test_case(LsvEncZeroHPattern())

    lsvscript.run()
