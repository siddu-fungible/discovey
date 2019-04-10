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


class ReplicaCryptoVolumeScript(FunTestScript):
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
        self.topology_obj_helper.cleanup()
        # pass


class ReplicaCryptoVolumeTestCase(FunTestCase):
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
        if ('expected_replica_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_replica_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal replica stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected replica volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_replica_stats))

        if ('expected_blt_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_blt_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal BLT stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected internal BLT stats for this {} testcase: \n{}".
                     format(testcase, self.expected_blt_stats))

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
        self.blt_delete_count = 0
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
        self.uuid["replica"] = []
        self.volume_list = []
        self.detach_count = 0

        self.blt_capacity = self.blt_details["capacity"] + 4096
        for i in range(1, self.blt_count + 1, 1):
            cur_uuid = utils.generate_uuid()
            self.uuid["blt"].append(cur_uuid)
            command_result = self.storage_controller.create_volume(type=self.vol_types["blt"],
                                                                   capacity=self.blt_capacity,
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(i),
                                                                   uuid=cur_uuid,
                                                                   command_duration=self.command_timeout)
            if not command_result["status"]:
                self.blt_creation_fail = True
                fun_test.test_assert(command_result["status"], "BLT creation with uuid {} & capacity {}".
                                     format(cur_uuid, self.blt_capacity))

        self.volume_list.append("blt")

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

        # Create replica volume
        self.uuid["replica"] = utils.generate_uuid()
        command_result = self.storage_controller.create_volume(type=self.vol_types["replica"],
                                                               capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="replica_vol",
                                                               uuid=self.uuid["replica"],
                                                               min_replicas_insync=1,
                                                               pvol_id=self.uuid["blt"],
                                                               encrypt=self.encrypt,
                                                               key=self.xts_key,
                                                               xtweak=self.xts_tweak,
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Replica vol "
                                                       "create with uuid {} & capacity {} using {} byte key".
                             format(self.uuid["replica"], self.blt_details["capacity"], key_size))

        command_result = self.storage_controller.volume_attach_remote(ns_id=self.ns_id,
                                                                      uuid=self.uuid["replica"],
                                                                      remote_ip=self.linux_host.internal_ip,
                                                                      command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Attach Replica with uuid {}".format(self.uuid["replica"]))
        self.attach_count = 1
        self.volume_list.append("replica")

        # Check the expected filter params
        if hasattr(self, "encrypt") and self.encrypt:
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

        # Disable the error_injection for the replica volume
        command_result = self.storage_controller.poke("params/repvol/error_inject 0")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"],
                             "Disabling error_injection for replica volume")
        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping after disabling the error_injection", 1)
        command_result = self.storage_controller.peek("params/repvol")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"],
                             "Retrieving error_injection status")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")

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
        self.fault_enabled = False

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

            if combo in self.expected_replica_stats:
                expected_replica_stats = self.expected_replica_stats[combo]
            else:
                expected_replica_stats = self.expected_replica_stats

            if combo in self.expected_blt_stats:
                expected_blt_stats = self.expected_blt_stats[combo]
            else:
                expected_blt_stats = self.expected_blt_stats

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

                if mode != "write" and not self.fault_enabled:
                    # Enable fault injection on the volume
                    if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
                        if self.plex_details["indices"] == "random":
                            fun_test.log("Using random plexes to trigger failure")
                            self.plex_indices = []
                            for x in range(1, self.plex_details["count"] + 1, 1):
                                while True:
                                    rand_num = random.randint(1, self.blt_count)
                                    if rand_num not in self.plex_indices:
                                        self.plex_indices.append(rand_num)
                                        break
                            self.plex_details["indices"] = self.plex_indices
                            fun_test.log("Triggering failure on {}".format(self.plex_details["indices"]))

                        for index in self.plex_details["indices"]:
                            command_result = self.storage_controller.fail_volume(uuid=self.uuid["blt"][index - 1],
                                                                                 command_duration=self.command_timeout)
                            fun_test.log(command_result)
                            fun_test.test_assert(command_result["status"], "Inject failure to BLT {} having the UUID {}"
                                                 .format(index, self.uuid["blt"][index - 1]))
                            fun_test.sleep("Sleeping after enabling fault_injection", 1)
                            props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.vol_types["blt"],
                                                                 self.uuid["blt"][index - 1], "stats")
                            command_result = self.storage_controller.peek(props_tree)
                            fun_test.log(command_result)
                            fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]),
                                                          expected=1,
                                                          message="Ensuring fault_injection got enabled")
                    self.fault_enabled = True

                for loop in range(0, self.fio_loop, 1):
                    fun_test.log("Running loop {} of {}".format((loop + 1), self.fio_loop))
                    initial_vol_stats[combo][mode] = {}
                    for vol_type in self.volume_list:
                        initial_vol_stats[combo][mode][vol_type] = {}
                        if vol_type == "blt":
                            # Loop through all BLT's
                            for x in range(1, self.blt_count + 1, 1):
                                cur_uuid = self.uuid["blt"][x - 1]
                                initial_vol_stats[combo][mode][vol_type][x] = {}
                                storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                             "volumes",
                                                                             self.vol_types["blt"],
                                                                             cur_uuid,
                                                                             "stats")
                                command_result = self.storage_controller.peek(storage_props_tree)
                                fun_test.simple_assert(command_result["status"], "Initial BLT {} stats of DUT".
                                                       format(x))
                                initial_vol_stats[combo][mode][vol_type][x] = command_result["data"]
                                fun_test.log("BLT {} stats at the beginning of the test:".format(x))
                                fun_test.log(initial_vol_stats[combo][mode][vol_type][x])
                        else:
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
                                                                        self.vol_types["replica"],
                                                                        self.uuid["replica"], x)

                            command_result = self.storage_controller.peek(crypto_props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats for Replica".
                                                   format(x))
                            if command_result["data"] is None:
                                command_result["data"] = 0
                            initial_crypto_stats[combo][mode][x] = command_result["data"]

                            fun_test.log("Replica : {} stats at the beginning of the test: {}".
                                         format(x, initial_crypto_stats[combo][mode][x]))

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
                        for x in range(1, self.parallel_count + 1, 1):
                            if mode == "rw" or mode == "randrw":
                                wait_time = self.parallel_count + 1 - x
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
                                wait_time = self.parallel_count + 1 - x
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
                        for x in range(1, self.parallel_count + 1, 1):
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
                        if vol_type == "blt":
                            # Loop through all BLT's
                            for x in range(1, self.blt_count + 1, 1):
                                cur_uuid = self.uuid["blt"][x - 1]
                                final_vol_stats[combo][mode][vol_type][x] = {}
                                storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                             "volumes",
                                                                             self.vol_types["blt"],
                                                                             cur_uuid,
                                                                             "stats")
                                command_result = self.storage_controller.peek(storage_props_tree)
                                fun_test.simple_assert(command_result["status"], "Final BLT {} stats of DUT".format(x))
                                final_vol_stats[combo][mode][vol_type][x] = command_result["data"]
                                fun_test.log("BLT {} stats at the end of the test:".format(x))
                                fun_test.log(final_vol_stats[combo][mode][vol_type][x])
                        else:
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
                        if vol_type == "blt":
                            # Loop through all BLT's
                            for x in range(1, self.blt_count + 1, 1):
                                diff_vol_stats[combo][mode][vol_type][x] = {}
                                for fkey, fvalue in final_vol_stats[combo][mode][vol_type][x].items():
                                    if fkey not in expected_blt_stats[mode] or fkey == "fault_injection":
                                        diff_vol_stats[combo][mode][vol_type][x][fkey] = fvalue
                                        continue
                                    if fkey in initial_vol_stats[combo][mode][vol_type][x]:
                                        ivalue = initial_vol_stats[combo][mode][vol_type][x][fkey]
                                        diff_vol_stats[combo][mode][vol_type][x][fkey] = fvalue - ivalue
                                    else:
                                        fun_test.simple_assert(False,
                                                               message="{} is not found in BLT {} inital stats".
                                                               format(fkey, x))
                                fun_test.log("Difference of BLT {} stats before and after the test:".format(x))
                                fun_test.log(diff_vol_stats[combo][mode][vol_type][x])
                        else:
                            if vol_type == "replica":
                                expected_vol_stats = expected_replica_stats[mode]
                            diff_vol_stats[combo][mode][vol_type] = {}
                            for fkey, fvalue in final_vol_stats[combo][mode][vol_type].items():
                                if fkey not in expected_vol_stats or fkey == "fault_injection":
                                    diff_vol_stats[combo][mode][vol_type][fkey] = fvalue
                                    continue
                                if fkey in initial_vol_stats[combo][mode][vol_type]:
                                    ivalue = initial_vol_stats[combo][mode][vol_type][fkey]
                                    diff_vol_stats[combo][mode][vol_type][fkey] = fvalue - ivalue
                                else:
                                    fun_test.simple_assert(False,
                                                           message="{} is not found in {} initial stats".
                                                           format(fkey, vol_type))
                            fun_test.log("Difference of {} stats before and after the test:".format(vol_type))
                            fun_test.log(diff_vol_stats[combo][mode][vol_type])

                    # Checking if the numbers match the expected value
                    for vol_type in self.volume_list:
                        if vol_type == "blt":
                            # Loop through all BLT's
                            for x in range(1, self.blt_count + 1, 1):
                                if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure and \
                                        self.fault_enabled:
                                    if x in self.plex_details["indices"]:
                                        for ekey in expected_blt_stats[mode].keys():
                                            if ekey == "fault_injection":
                                                evalue = 1
                                            else:
                                                evalue = 0
                                            actual = diff_vol_stats[combo][mode][vol_type][x][ekey]
                                            fun_test.test_assert_expected(evalue, actual,
                                                                          message="Final {} value for BLT {} for "
                                                                                  "mode {} & combo {}".
                                                                          format(ekey, x, mode, combo))
                                else:
                                    for ekey, evalue in expected_blt_stats[mode].items():
                                        actual = diff_vol_stats[combo][mode][vol_type][x][ekey]
                                        if ekey == "num_reads":
                                            active_plex = int(evalue[0])
                                            idle_plex = int(evalue[1])
                                            if actual == active_plex:
                                                fun_test.test_assert_expected(active_plex, actual,
                                                                              "BLT {} is active, final {} for mode {} "
                                                                              "& combo {}".
                                                                              format(x, ekey, mode, combo))
                                            elif actual == idle_plex:
                                                fun_test.test_assert_expected(idle_plex, actual,
                                                                              "BLT {} is idle, final {} for mode {} "
                                                                              "& combo {}".
                                                                              format(x, ekey, mode, combo))
                                            else:
                                                fun_test.simple_assert(False, "Final {} value of {} for BLT {} not in"
                                                                              "expected value".
                                                                       format(ekey, actual, x))
                                        else:
                                            fun_test.test_assert_expected(evalue, actual,
                                                                          message="Final {} value for BLT {} for "
                                                                                  "mode {} & combo {}".
                                                                          format(ekey, x, mode, combo))
                        else:
                            if vol_type == "replica":
                                expected_vol_stats = expected_replica_stats[mode]
                            for ekey, evalue in expected_vol_stats.items():
                                actual = diff_vol_stats[combo][mode][vol_type][ekey]
                                fun_test.test_assert_expected(evalue, actual,
                                                              message="Final {} value for Replica vol {} for "
                                                                      "mode {} & combo {}".
                                                              format(ekey, self.uuid["replica"], mode, combo))

                    if hasattr(self, "encrypt") and self.encrypt:
                        final_crypto_stats[combo][mode] = {}
                        diff_crypto_stats[combo][mode] = {}
                        for x in self.crypto_ops:
                            diff_crypto_stats[combo][mode][x] = {}
                            final_crypto_stats[combo][mode][x] = {}
                            crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                        self.vol_types["replica"],
                                                                        self.uuid["replica"], x)

                            command_result = self.storage_controller.peek(crypto_props_tree)
                            fun_test.simple_assert(command_result["status"], "Final {} stats for Replica".
                                                   format(x))
                            final_crypto_stats[combo][mode][x] = command_result["data"]
                            fun_test.log("Replica : {} stats at the end of the test: {}".
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
                            fun_test.log("Difference of Replica {} stats before and after the test: {}".
                                         format(x, diff_crypto_stats[combo][mode][x]))

                            for ekey, evalue in expected_crypto_stats.items():
                                if ekey in diff_crypto_stats[combo][mode][x]:
                                    actual = diff_crypto_stats[combo][mode][x][ekey]
                                    fun_test.test_assert_expected(evalue, actual,
                                                                  message="{} : {} stats for {} mode & {} combo on "
                                                                          "Replica".format(x, ekey, mode, combo))
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

    def cleanup(self):
        if hasattr(self, "host_disconnect") and self.host_disconnect:
            self.linux_host.disconnect()

        if not self.blt_creation_fail:
            command_result = self.storage_controller.volume_detach_remote(ns_id=self.ns_id,
                                                                          uuid=self.uuid["replica"],
                                                                          remote_ip=self.linux_host.internal_ip)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detach replica with uuid {}".format(self.uuid["replica"]))

            command_result = self.storage_controller.delete_volume(name="replica_vol",
                                                                   uuid=self.uuid["replica"],
                                                                   type=self.vol_types["replica"])
            fun_test.test_assert(command_result["status"], "Deleting replica vol with uuid {}".
                                 format(self.uuid["replica"]))

        for x in range(1, self.blt_count + 1, 1):
            cur_uuid = self.uuid["blt"][x - 1]
            command_result = self.storage_controller.delete_volume(name="thin_block" + str(x),
                                                                   uuid=cur_uuid,
                                                                   type=self.vol_types["blt"])
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_delete_count += 1
            else:
                fun_test.test_assert(not command_result["status"], "Deleting BLT {} with uuid {}".
                                     format(x, cur_uuid))
        fun_test.test_assert_expected(self.blt_count, self.blt_delete_count,
                                      message="BLT count & delete count")

        # Verify cleanup is successful
        for vol_type in self.volume_list:
            if vol_type == "blt":
                for x in range(1, self.blt_count + 1, 1):
                    cur_uuid = self.uuid["blt"][x - 1]
                    storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                              self.vol_types[vol_type], cur_uuid)
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(expression=command_result["data"] is None,
                                           message="BLT {} with uuid {} removal".format(x, cur_uuid))
            else:
                storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                          self.vol_types[vol_type], self.uuid[vol_type])
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(expression=command_result["data"] is None,
                                       message="{} with uuid {} removal".format(vol_type, self.uuid[vol_type]))


class ReplicaKey256(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="2 way replica with 256 bit key and run FIO with different RW pattern(write,read,"
                                      "randwrite,randread), with different block size & depth",
                              steps='''
                              1. Create a replica with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey256RW(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="3 way replica with 256 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a replica with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey256RandRW(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="4 way replica with 256 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a replica with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey256RandRW50(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="5 way replica with 256 bit key and run FIO RandRW(50%RW) pattern "
                                      "with different block size & depth",
                              steps='''
                              1. Create a replica with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey256RandRW70(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="5 way replica with 256 bit key and run FIO RandRW(70:30::R:W) pattern "
                                      "with different block size & depth",
                              steps='''
                              1. Create a replica with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey512(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="2 way replica with 512 bit key and run FIO with different RW pattern(write,read,"
                                      "randwrite,randread), with different block size & depth",
                              steps='''
                              1. Create a replica with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey512RW(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="3 way replica with 512 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a replica with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey512RandRW(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="4 way replica with 512 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a replica with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey512RandRW50(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="5 way replica with 512 bit key and run FIO RandRW(50%RW) pattern with different"
                                      " block size & depth",
                              steps='''
                              1. Create a replica with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


class ReplicaKey512RandRW70(ReplicaCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="5 way replica with 512 bit key and run FIO RandRW(70:30::R:W) pattern with "
                                      "different block size & depth",
                              steps='''
                              1. Create a replica with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')


if __name__ == "__main__":
    replicascript = ReplicaCryptoVolumeScript()
    replicascript.add_test_case(ReplicaKey256())
    replicascript.add_test_case(ReplicaKey256RW())
    replicascript.add_test_case(ReplicaKey256RandRW())
    replicascript.add_test_case(ReplicaKey256RandRW50())
    replicascript.add_test_case(ReplicaKey256RandRW70())
    replicascript.add_test_case(ReplicaKey512())
    replicascript.add_test_case(ReplicaKey512RW())
    replicascript.add_test_case(ReplicaKey512RandRW())
    replicascript.add_test_case(ReplicaKey512RandRW50())
    replicascript.add_test_case(ReplicaKey512RandRW70())

    replicascript.run()
