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


# Disconnect linux objects
def fio_parser(arg1, **kwargs):
    arg1.remote_fio(**kwargs)
    arg1.disconnect()


class BLTCryptoVolumeScript(FunTestScript):
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


class BLTCryptoVolumeTestCase(FunTestCase):
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
        fun_test.test_assert(benchmark_parsing, "Parsing testcase json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))

        if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
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
        key512_count = 0
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0
        self.correct_key_tweak = None
        self.blt_creation_fail = None

        # Configuring local thin block volume
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")
        # Configuring controller
        if not fun_test.shared_variables["ctrl_created"]:
            command_result = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip,
                                                            command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on Dut".
                                 format(self.dut_instance.data_plane_ip))
            fun_test.shared_variables["ctrl_created"] = True

        self.thin_uuid = {}
        self.block_size = {}
        self.vol_capacity = {}
        self.encrypted_vol = {}
        bs_auto = None
        capacity_auto = None

        if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
            initial_filter_values = {}
            for filter_param in self.filter_params:
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = self.storage_controller.peek(crypto_props_tree)
                if command_result["data"] is None:
                    command_result["data"] = 0
                initial_filter_values[filter_param] = command_result["data"]

        for x in range(1, self.volume_count + 1, 1):
            self.thin_uuid[x] = utils.generate_uuid()
            # Key generation for encryption based on size or input is random or alternate
            if self.key_size == "random":
                key_range = [32, 64]
                rand_key = random.choice(key_range)
                self.xts_key = utils.generate_key(rand_key)
                if rand_key == 32:
                    key256_count += 1
                else:
                    key512_count += 1
            elif self.key_size == "alternate":
                if x % 2:
                    key256_count += 1
                    self.xts_key = utils.generate_key(32)
                else:
                    key512_count += 1
                    self.xts_key = utils.generate_key(64)
            else:
                self.xts_key = utils.generate_key(self.key_size)
            self.xts_tweak = utils.generate_key(self.xtweak_size)

            # Select volume block size from a range
            if self.volume_details["block_size"] == "Auto":
                bs_auto = True
                self.block_size[x] = random.choice(self.volume_details["block_size_range"])
                self.volume_details["block_size"] = self.block_size[x]

            # Select volume capacity from a range
            if self.volume_details["capacity"] == "Auto":
                capacity_auto = True
                self.vol_capacity[x] = random.choice(self.volume_details["capacity_range"])
                self.volume_details["capacity"] = self.vol_capacity[x]
                check_cap = self.volume_details["capacity"] % self.volume_details["block_size"]
                fun_test.simple_assert(expression=check_cap == 0,
                                       message="Capacity should be multiple of block size.")
            # Here you cannot use boolean coz when encryption is set to alternate in json the value always
            # returns true as something is assigned to it.
            if self.volume_details["encrypt"] == "enable":
                self.vol_encrypt = True
                self.encrypted_vol[x] = self.thin_uuid[x]
            elif self.volume_details["encrypt"] == "disable":
                self.vol_encrypt = False
            elif self.volume_details["encrypt"] == "alternate":
                if x % 2:
                    self.vol_encrypt = True
                    self.encrypted_vol[x] = self.thin_uuid[x]
                else:
                    self.vol_encrypt = False
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   name="thin_block" + str(x),
                                                                   uuid=self.thin_uuid[x],
                                                                   encrypt=self.vol_encrypt,
                                                                   key=self.xts_key,
                                                                   xtweak=self.xts_tweak,
                                                                   command_duration=self.command_timeout)
            if bs_auto:
                self.volume_details["block_size"] = "Auto"
            if capacity_auto:
                self.volume_details["capacity"] = "Auto"

            # Attach volume only if encryption is disabled or key/tweak sizes are sane
            if (self.key_size == 32 or self.key_size == 64 or self.key_size == "random" or self.key_size == "alternate"
                or not self.vol_encrypt) and self.xtweak_size == 8:
                self.correct_key_tweak = True
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"], "BLT {} creation with uuid {} & capacity {}".
                                         format(x, self.thin_uuid[x], self.volume_details["capacity"]))

                command_result = self.storage_controller.volume_attach_remote(ns_id=x,
                                                                              uuid=self.thin_uuid[x],
                                                                              remote_ip=self.linux_host.internal_ip,
                                                                              command_duration=self.command_timeout)
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_attach_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Attach BLT {} with uuid {}".
                                         format(x, self.thin_uuid[x]))
            elif self.vol_encrypt:
                fun_test.test_assert(not command_result["status"],
                                     message="BLT creation should fail")
                self.blt_creation_fail = True
            else:
                self.blt_create_count += 1
                fun_test.test_assert(command_result["status"], "BLT {} creation with uuid {} & capacity {} "
                                                               "with encryption disabled".
                                     format(x, self.thin_uuid[x], self.volume_details["capacity"]))

        if self.key_size == "random" or self.key_size == "alternate":
            fun_test.log("Total BLT with 256 bit key: {}".format(key256_count))
            fun_test.log("Total BLT with 512 bit key: {}".format(key512_count))
        if not self.blt_creation_fail:
            fun_test.test_assert_expected(self.volume_count, self.blt_create_count,
                                          message="BLT count and create count")
        if self.correct_key_tweak:
            fun_test.test_assert_expected(self.volume_count, self.blt_attach_count,
                                          message="BLT count and attach count")

            # Check the expected filter params only if its correct key & tweak
            if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
                final_filter_values = {}
                diff_filter_values = {}
                for filter_param in self.filter_params:
                    crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                    command_result = self.storage_controller.peek(crypto_props_tree)
                    if command_result["data"] is None:
                        command_result["data"] = 0
                    final_filter_values[filter_param] = command_result["data"]
                    if len(self.encrypted_vol) > 1:
                        multiplier = len(self.encrypted_vol)
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
                                                  message="Comparing crypto filter : {} count".format(filter_param))

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_output = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}
        diff_volume_stats = {}
        diff_crypto_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}

        for combo in self.fio_bs_iodepth:
            fio_output[combo] = {}
            final_volume_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}
            diff_volume_stats[combo] = {}
            diff_crypto_stats[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
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
                    initial_volume_stats[combo][mode] = {}
                    for x in range(1, self.volume_count + 1, 1):
                        initial_volume_stats[combo][mode][x] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial BLT {} stats of DUT".format(x))
                        initial_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("BLT {} Stats at the beginning of the test: {}".
                                     format(x, initial_volume_stats[combo][mode][x]))

                    initial_crypto_stats[combo][mode] = {}
                    if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
                        self.crypto_ops = ["encryption", "decryption"]
                        for i in self.encrypted_vol:
                            initial_crypto_stats[combo][mode][i] = {}
                            for x in self.crypto_ops:
                                initial_crypto_stats[combo][mode][i][x] = {}
                                crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                            "VOL_TYPE_BLK_LOCAL_THIN",
                                                                            self.thin_uuid[i], x)

                                command_result = self.storage_controller.peek(crypto_props_tree)
                                fun_test.simple_assert(command_result["status"], "Initial {} stats for BLT {}".
                                                       format(x, i))
                                if command_result["data"] is None:
                                    command_result["data"] = 0
                                initial_crypto_stats[combo][mode][i][x] = command_result["data"]

                                fun_test.log("BLT {} crypto stats at the beginning of the test: {}".
                                             format(i, initial_crypto_stats[combo][mode][i]))

                    if not self.traffic_parallel:
                        for x in range(1, self.volume_count + 1, 1):
                            if mode == "rw" or mode == "randrw":
                                fio_output[combo][mode] = {}
                                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                     rw=mode,
                                                                                     bs=fio_block_size,
                                                                                     iodepth=fio_iodepth,
                                                                                     rwmixread=self.fio_rwmixread,
                                                                                     nsid=x,
                                                                                     **self.fio_cmd_args)
                                fun_test.test_assert(fio_output[combo][mode],
                                                     "Fio test on nsid {} completed for {} mode & {} combo".
                                                     format(x, mode, combo))
                                fun_test.log("FIO Command Output:")
                                fun_test.log(fio_output[combo][mode])
                                self.linux_host.disconnect()
                            else:
                                fio_output[combo][mode] = {}
                                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                     rw=mode,
                                                                                     bs=fio_block_size,
                                                                                     iodepth=fio_iodepth,
                                                                                     nsid=x,
                                                                                     **self.fio_cmd_args)
                                fun_test.test_assert(fio_output[combo][mode],
                                                     "Fio test on nsid {} completed for {} mode & {} combo".
                                                     format(x, mode, combo))
                                fun_test.log("FIO Command Output:")
                                fun_test.log(fio_output[combo][mode])
                                self.linux_host.disconnect()
                    else:
                        fun_test.log("Running fio test is threaded mode...")
                        thread_id = {}
                        wait_time = 0
                        for x in range(1, self.volume_count + 1, 1):
                            if mode == "rw" or mode == "randrw":
                                wait_time = self.volume_count + 1 - x
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
                                fun_test.sleep("Fio threadzz", seconds=1)
                            else:
                                wait_time = self.volume_count + 1 - x
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
                        for x in range(1, self.volume_count + 1, 1):
                            fun_test.log("Joining thread {}".format(x))
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])

                        if self.linux_host.command("pgrep fio"):
                            timer_kill = FunTimer(max_time=self.fio_cmd_args["timeout"] * 2)
                            while not timer_kill.is_expired():
                                if not self.linux_host.command("pgrep fio"):
                                    break
                                else:
                                    fun_test.sleep("Waiting for fio to exit...sleeping 10 secs", seconds=10)

                            fun_test.log("Timer expired, killing fio...")
                            self.linux_host.command("for i in `pgrep fio`;do kill -9 $i;done")
                        self.linux_host.disconnect()

                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

                    # Getting final stats
                    final_volume_stats[combo][mode] = {}
                    diff_volume_stats[combo][mode] = {}
                    for x in range(1, self.volume_count + 1, 1):
                        final_volume_stats[combo][mode][x] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                     "volumes",
                                                                     "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Final BLT {} stats of DUT".format(x))
                        final_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("BLT {} stats at the end of the test: {}".
                                     format(x, final_volume_stats[combo][mode][x]))

                        diff_volume_stats[combo][mode][x] = {}
                        for fkey, fvalue in final_volume_stats[combo][mode][x].items():
                            if fkey not in expected_volume_stats[mode] or fkey == "fault_injection":
                                diff_volume_stats[combo][mode][x][fkey] = fvalue
                                continue
                            if fkey in initial_volume_stats[combo][mode][x]:
                                ivalue = initial_volume_stats[combo][mode][x][fkey]
                                diff_volume_stats[combo][mode][x][fkey] = fvalue - ivalue
                        fun_test.log("Difference of BLT {} stats before and after the test: {}".
                                     format(x, diff_volume_stats[combo][mode][x]))

                        for ekey, evalue in expected_volume_stats[mode].items():
                            if ekey in diff_volume_stats[combo][mode][x]:
                                actual = diff_volume_stats[combo][mode][x][ekey]
                                fun_test.test_assert_expected(evalue, actual,
                                                              message="{} check for {} mode & {} combo on BLT {}".
                                                              format(ekey, mode, combo, x))
                            else:
                                fun_test.critical("{} is not found in BLT stats".format(ekey))
                                fun_test.add_checkpoint("{} not found in BLT {} stats".format(ekey, x),
                                                        "FAILED",
                                                        ekey,
                                                        "Not found")

                    final_crypto_stats[combo][mode] = {}
                    diff_crypto_stats[combo][mode] = {}
                    if self.volume_details["encrypt"] == "enable" or self.volume_details["encrypt"] == "alternate":
                        for i in self.encrypted_vol:
                            final_crypto_stats[combo][mode][i] = {}
                            diff_crypto_stats[combo][mode][i] = {}
                            for x in self.crypto_ops:
                                diff_crypto_stats[combo][mode][i][x] = {}
                                final_crypto_stats[combo][mode][i][x] = {}
                                crypto_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                            "VOL_TYPE_BLK_LOCAL_THIN",
                                                                            self.thin_uuid[i], x)

                                command_result = self.storage_controller.peek(crypto_props_tree)
                                fun_test.simple_assert(command_result["status"], "Final {} stats for BLT {}".
                                                       format(x, i))
                                final_crypto_stats[combo][mode][i][x] = command_result["data"]
                                fun_test.log("BLT {} : {} stats at the end of the test: {}".
                                             format(i, x, final_crypto_stats[combo][mode][i]))

                                if x == "encryption":
                                    expected_crypto_stats = expected_encryption_stats[mode]
                                elif x == "decryption":
                                    expected_crypto_stats = expected_decryption_stats[mode]

                                for fkey, fvalue in final_crypto_stats[combo][mode][i][x].items():
                                    if fkey not in expected_crypto_stats:
                                        diff_crypto_stats[combo][mode][i][x][fkey] = fvalue
                                        continue
                                    if fkey in initial_crypto_stats[combo][mode][i][x]:
                                        ivalue = initial_crypto_stats[combo][mode][i][x][fkey]
                                        diff_crypto_stats[combo][mode][i][x][fkey] = fvalue - ivalue
                                fun_test.log("Difference of BLT {} {} stats before and after the test: {}".
                                             format(i, x, diff_crypto_stats[combo][mode][i][x]))

                                for ekey, evalue in expected_crypto_stats.items():
                                    if ekey in diff_crypto_stats[combo][mode][i][x]:
                                        actual = diff_crypto_stats[combo][mode][i][x][ekey]
                                        fun_test.test_assert_expected(evalue, actual,
                                                                      message="{} : {} stats for {} mode & {} combo on "
                                                                              "BLT {}".format(x, ekey, mode, combo, i))
                                    else:
                                        fun_test.critical("{} is not found in BLT {} {} stats".format(ekey, i, x))
                                        fun_test.add_checkpoint("{} not found in {} diff_crypto_stats on BLT {}".
                                                                format(ekey, x, i), "FAILED", ekey, "Not found")

                        if hasattr(self, "crypto_ops_params"):
                            filter_values = []
                            for i in self.crypto_ops_params:
                                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", i)
                                command_result = self.storage_controller.peek(crypto_props_tree)
                                filter_values.append(command_result["data"])

                            fun_test.simple_assert(expression=len(filter_values) != len(set(filter_values)),
                                                   message="There seems to be difference in crypto filter stats {}".
                                                   format(filter_values))

                    # Moved the detach loop here as the BLT crypto stats get reset to 0 during detach/attach
                    if self.detach_vol:
                        fun_test.sleep("Sleeping for {} seconds before detach/attach".format(self.iter_interval),
                                       self.iter_interval)
                        for x in range(1, self.volume_count + 1, 1):
                            command_result = self.storage_controller.volume_detach_remote(
                                ns_id=x,
                                uuid=self.thin_uuid[x],
                                remote_ip=self.linux_host.internal_ip)
                            fun_test.log(command_result)
                            fun_test.simple_assert(command_result["status"],
                                                   message="Detach failed for test {} with combo {}".
                                                   format(mode, combo))

                            command_result = self.storage_controller.volume_attach_remote(
                                ns_id=x,
                                uuid=self.thin_uuid[x],
                                remote_ip=self.linux_host.internal_ip,
                                command_duration=self.command_timeout)
                            fun_test.log(command_result)
                            fun_test.simple_assert(command_result["status"],
                                                   message="Attach failed for test {} with combo {}".
                                                   format(mode, combo))

    def cleanup(self):
        bs_auto = None
        capacity_auto = None
        self.linux_host.disconnect()

        if not self.blt_creation_fail:
            # Not using attach count as for TC 17 attach is not done but still BLT is created.
            for x in range(1, self.blt_create_count + 1, 1):
                if self.correct_key_tweak:
                    command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                                  uuid=self.thin_uuid[x],
                                                                                  remote_ip=self.linux_host.internal_ip)
                    fun_test.log(command_result)
                    if command_result["status"]:
                        self.blt_detach_count += 1
                    else:
                        fun_test.test_assert(command_result["status"], "Detach BLT {} with uuid {}".
                                             format(x, self.thin_uuid[x]))

                if self.volume_details["block_size"] == "Auto":
                    bs_auto = True
                    self.volume_details["block_size"] = self.block_size[x]

                if self.volume_details["capacity"] == "Auto":
                    capacity_auto = True
                    self.volume_details["capacity"] = self.vol_capacity[x]

                command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                                       block_size=self.volume_details["block_size"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=self.thin_uuid[x],
                                                                       type="VOL_TYPE_BLK_LOCAL_THIN")
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_delete_count += 1
                else:
                    fun_test.test_assert(not command_result["status"], "Delete BLT {} with uuid {}".
                                         format(x, self.thin_uuid[x]))

                if bs_auto:
                    self.volume_details["block_size"] = "Auto"
                if capacity_auto:
                        self.volume_details["capacity"] = "Auto"

            if self.correct_key_tweak:
                fun_test.test_assert_expected(self.volume_count, self.blt_detach_count,
                                              message="BLT count & detach count")

            fun_test.test_assert_expected(self.volume_count, self.blt_delete_count,
                                          message="BLT count & delete count")

            for x in range(1, self.volume_count + 1, 1):
                storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes",
                                                          "VOL_TYPE_BLK_LOCAL_THIN", self.thin_uuid[x])
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(expression=command_result["data"] is None,
                                       message="BLT {} with uuid {} removal".format(x, self.thin_uuid[x]))


class BLTKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a volume with 256 bit key and run FIO on single BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a local thin block volume with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create BLT's with encryption using 256 bit key & run RW test on single volume "
                                      "using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create BLT's with encryption using 256 bit key & run RandRW test using "
                                      "different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create a volume with 512 bit key and run FIO on single BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a local thin block volume with encryption using 512 bit key on DUT.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Create BLT's with encryption using 512 bit key & run RW test on single volume "
                                      "using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class BLTKey512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create BLT's with encryption using 512 bit key & run RandRW test on single "
                                      "volume using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class WrongKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create BLT's with wrong size key",
                              steps='''
                              1. Create a BLT with encryption using unsupported key in dut.
        ''')

    def run(self):
        pass


class WrongTweak(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Create BLT's with wrong size tweak",
                              steps='''
                              1. Create a BLT with encryption using unsupported tweak in dut.
        ''')

    def run(self):
        pass


class CreateDelete256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Create, attach & delete 25 BLT's with encryption using 256 size key",
                              steps='''
                              1. Create BLT's with encryption with 256 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def run(self):
        pass


class CreateDelete512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Create, attach & delete 25 BLT's with encryption using 512 size key",
                              steps='''
                              1. Create BLT's with encryption with 512 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def run(self):
        pass


class MultipleBLT256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Create BLT's with 256 bit key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=13,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RandRW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=14,
                              summary="Create BLT's with 512 bit key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=15,
                              summary="Create multiple BLT's with encryption using 512 bit key & run FIO in parallel "
                                      "on all BLT RW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class MultipleBLT512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=16,
                              summary="Create multiple BLT's with encryption using 256 bit key & run FIO in parallel "
                                      "on all BLT RandRW tests using different block size & depth",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')


class EncryptDisable(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=17,
                              summary="Create BLT's with wrong size key/tweak with encryption disabled",
                              steps='''
                              1. Create a BLT with encryption disabled using unsupported tweak in dut.
                              2. Creation of BLT should pass as encryption is disabled.
        ''')

    def run(self):
        pass


class BLTRandomKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=18,
                              summary="Create BLT's with random key and run FIO on multiple BLT with write,read,"
                                      "randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create a BLT with encryption using random key in dut.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')


class MultiVolRandKeyRandCap(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=19,
                              summary="Create BLT's with random key & capacity and run FIO on single BLT with write,"
                                      "read,randwrite/read pattern, block size & depth",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
        ''')


class BLTFioDetach(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=20,
                              summary="Create BLT's with random key & capacity & run FIO in parallel with write,read,"
                                      "randwrite/read pattern, block size & depth with detach after each iteration",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTFioEncZeroPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=21,
                              summary="Encrypt multiple BLT with random key and run fio with different RW pattern,"
                                      "(write,read,randwrite/read), block size & depth with 0x000000000 pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTFioEncDeadBeefPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=22,
                              summary="Encrypt multiple BLT with random key and run fio with different RW pattern"
                                      "(write,read,randwrite/read),block size & depth with DEADBEEF pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


class BLTAlternateEncrypt(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=23,
                              summary="Encrypt alternate BLT with random key & run fio with different RW pattern"
                                      "(write,read,randwrite/read),block size & depth with DEADBEEF pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(BLTKey256())
    bltscript.add_test_case(BLTKey256RW())
    bltscript.add_test_case(BLTKey256RandRW())
    bltscript.add_test_case(BLTKey512())
    bltscript.add_test_case(BLTKey512RW())
    bltscript.add_test_case(BLTKey512RandRW())
    bltscript.add_test_case(WrongKey())
    bltscript.add_test_case(WrongTweak())
    bltscript.add_test_case(CreateDelete256())
    bltscript.add_test_case(CreateDelete512())
    bltscript.add_test_case(MultipleBLT256())
    bltscript.add_test_case(MultipleBLT256RW())
    bltscript.add_test_case(MultipleBLT256RandRW())
    bltscript.add_test_case(MultipleBLT512())
    bltscript.add_test_case(MultipleBLT512RW())
    bltscript.add_test_case(MultipleBLT512RandRW())
    bltscript.add_test_case(EncryptDisable())
    bltscript.add_test_case(BLTRandomKey())
    bltscript.add_test_case(MultiVolRandKeyRandCap())
    bltscript.add_test_case(BLTFioDetach())
    bltscript.add_test_case(BLTFioEncZeroPattern())
    bltscript.add_test_case(BLTFioEncDeadBeefPattern())
    bltscript.add_test_case(BLTAlternateEncrypt())

    bltscript.run()
