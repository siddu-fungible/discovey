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


class ECCryptoVolumeScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        # self.topology_obj_helper.save(file_name="/tmp/pickle.pkl")
        # self.topology = self.topology_obj_helper.load(file_name="/tmp/pickle.pkl")
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut_instance = self.topology.get_dut_instance(index=0)
        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)
        # We have declared this here since when we remove volume, the counters are from zero but crypto
        # counters are not from zero.
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["total_lsv_ops"] = 0
        fun_test.shared_variables["crypto_filter_count"] = 0
        fun_test.shared_variables["compress_filter_count"] = 0
        fun_test.shared_variables["ctrl_created"] = False

    def cleanup(self):
        self.storage_controller.disconnect()
        TopologyHelper(spec=self.topology).cleanup()
        # pass


class ECCryptoVolumeTestCase(FunTestCase):
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
        if ('expected_lsv_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_lsv_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal lsv stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_lsv_stats))

        if 'blt_pass_threshold' not in testcase_dict[testcase]:
            self.blt_pass_threshold = 20
            fun_test.log("Setting blt passing threshold number to {} for this {} testcase, because its not set in "
                         "the {} file".format(self.blt_pass_threshold, testcase, testcase_file))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance = self.topology.get_dut_instance(index=0)
        self.linux_host = self.topology.get_tg_instance(tg_index=0)

        self.linux_host_inst = {}
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        key256_count = 0
        key512_count = 0
        self.blt_create_count = 0
        self.blt_delete_count = 0
        self.blt_capacity = 0
        self.uuid_list = []
        self.blt_creation_fail = None

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False

            # Configuring EC volume
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

            # Configuring controller
            if not fun_test.shared_variables["ctrl_created"]:
                command_result = {}
                command_result = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip,
                                                                command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT".
                                     format(self.dut_instance.data_plane_ip))
                fun_test.shared_variables["ctrl_created"] = True

            command_result = {}
            self.blt_count = self.ndata + self.nparity
            fun_test.shared_variables["blt_count"] = self.blt_count + 1
            self.blt_uuid = {}

            # LSV should be 70% of BLT capacity. So increase the BLT capacity by 30% and use BLT capacity for LSV.
            # Make sure the capacity is multiple of block size
            # EC vol capacity will be the same as new BLT capacity
            self.blt_capacity = (self.blt_details["capacity"] * self.lsv_head / 100) + self.blt_details["capacity"]
            if self.blt_capacity % self.blt_details["block_size"]:
                fun_test.log("Aligning BLT capacity to block size")
                mod_value = self.blt_capacity % self.blt_details["block_size"]
                self.blt_capacity += self.blt_details["block_size"] - mod_value

            for x in range(1, fun_test.shared_variables["blt_count"], 1):
                self.blt_uuid[x] = utils.generate_uuid()

                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                       capacity=self.blt_capacity,
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=self.blt_uuid[x],
                                                                       command_duration=self.command_timeout)

                if command_result:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"], "BLT {} creation on DUT".format(x))
                    self.blt_creation_fail = True

                self.uuid_list.append(self.blt_uuid[x])

            # Create EC Vol from updated blt capacity multiplied by ndata count
            self.ec_uuid = []
            self.ec_uuid = utils.generate_uuid()
            self.ec_capacity = self.blt_capacity * self.ndata
            command_result = {}
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_EC",
                                                                   capacity=self.ec_capacity,
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="ec_vol1",
                                                                   uuid=self.ec_uuid,
                                                                   ndata=self.ndata,
                                                                   nparity=self.nparity,
                                                                   pvol_id=self.uuid_list,
                                                                   command_duration=self.command_timeout)

            # Create JVol
            # The minimum jvol_capacity requirement is LSV chunk size * block size * 4
            # For current script we have hardcoded this 32 * 4096 * 4 as input
            if self.jvol_create:
                self.jvol_uuid = utils.generate_uuid()
                command_result = {}
                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_NV_MEMORY",
                                                                       capacity=self.jvol_details["capacity"],
                                                                       block_size=self.jvol_details["block_size"],
                                                                       name="jvol1",
                                                                       uuid=self.jvol_uuid,
                                                                       command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Jvol creation on DUT")

            # Key generation for encryption based on size or input is random or alternate
            if self.key_size == "random":
                key_range = [32, 64]
                rand_key = random.choice(key_range)
                self.xts_key = utils.generate_key(rand_key)
                if rand_key == 32:
                    key256_count += 1
                else:
                    key512_count += 1
            else:
                self.xts_key = utils.generate_key(self.key_size)

            self.xts_tweak = utils.generate_key(self.xtweak_size)

            # Create LSV Vol from blt capacity multiplied by ndata count
            if self.lsv_create:
                self.lsv_uuid = utils.generate_uuid()
                self.lsv_capacity = self.blt_details["capacity"] * self.ndata
                self.lsv_blocksize = self.blt_details["block_size"]
                if self.compress:
                    command_result = {}
                    command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LSV",
                                                                           capacity=self.lsv_capacity,
                                                                           block_size=self.lsv_blocksize,
                                                                           name="lsv1",
                                                                           uuid=self.lsv_uuid,
                                                                           jvol_uuid=self.jvol_uuid,
                                                                           pvol_id=[self.ec_uuid],
                                                                           group=self.ndata,
                                                                           encrypt=self.encrypt,
                                                                           key=self.xts_key,
                                                                           xtweak=self.xts_tweak,
                                                                           compress=self.compress,
                                                                           zip_filter=self.zip_filter,
                                                                           zip_effort=self.zip_effort,
                                                                           command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "LSV creation with compression & encryption")
                else:
                    command_result = {}
                    command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LSV",
                                                                           capacity=self.lsv_capacity,
                                                                           block_size=self.lsv_blocksize,
                                                                           name="lsv1",
                                                                           uuid=self.lsv_uuid,
                                                                           jvol_uuid=self.jvol_uuid,
                                                                           pvol_id=[self.ec_uuid],
                                                                           group=self.ndata,
                                                                           encrypt=self.encrypt,
                                                                           key=self.xts_key,
                                                                           xtweak=self.xts_tweak,
                                                                           command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "LSV creation with encryption")

                if self.traffic_parallel:
                    self.attach_count = self.parallel_count + 1
                    for x in range(1, self.attach_count, 1):
                        command_result = {}
                        command_result = self.storage_controller.volume_attach_remote(
                            ns_id=x,
                            uuid=self.lsv_uuid,
                            remote_ip=self.linux_host.internal_ip,
                            command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        if not command_result["status"]:
                            fun_test.test_assert(command_result["status"], "LSV attach {}".format(x))
                        else:
                            if self.compress:
                                fun_test.shared_variables["compress_filter_count"] += 2
                            if self.encrypt:
                                fun_test.shared_variables["crypto_filter_count"] += 2
                else:
                    command_result = {}
                    command_result = self.storage_controller.volume_attach_remote(ns_id=self.ns_id,
                                                                                  uuid=self.lsv_uuid,
                                                                                  remote_ip=self.linux_host.internal_ip,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "LSV attach")
                    if self.compress:
                        fun_test.shared_variables["compress_filter_count"] += 2
                    if self.encrypt:
                        fun_test.shared_variables["crypto_filter_count"] += 2

                # Disable the error_injection for the EC volume
                command_result = {}
                command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Disabling error_injection for EC volume on DUT instance 0")
                # Ensuring that the error_injection got disabled properly
                fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
                command_result = {}
                command_result = self.storage_controller.peek("params/ecvol")
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Retrieving error_injection status on DUT instance 0")
                fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                              message="Ensuring error_injection got disabled")

                fun_test.shared_variables["ec"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        total_vol_reads = 0
        total_vol_writes = 0

        crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", "cryptofilter_aes_xts")
        crypto_cluster_props_tree = "{}/{}/{}".format("stats", "crypto", "crypto_alg_stats")

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}
        diff_lsv_stats = {}
        diff_crypto_stats = {}
        initial_lsv_stats = {}
        final_lsv_stats = {}
        final_encrypted_vol_stats = {}

        # Check any plex needs to be induced to fail and if so do the same
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = self.storage_controller.fail_volume(uuid=self.blt_uuid[index],
                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                               "UUID {}".format(self.blt_uuid[index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                     self.blt_uuid[index], "stats")
                command_result = self.storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                              message="Ensuring fault_injection got enabled")

        command_result = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        fun_test.log("Crypto Stats at the beginning of the test:")
        fun_test.log(command_result["data"])

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            final_lsv_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}
            diff_lsv_stats[combo] = {}
            diff_crypto_stats[combo] = {}
            initial_lsv_stats[combo] = {}
            final_encrypted_vol_stats[combo] = {}

            if combo in self.expected_lsv_stats:
                expected_lsv_stats = self.expected_lsv_stats[combo]
            else:
                expected_lsv_stats = self.expected_lsv_stats

            for mode in self.fio_modes:
                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                for loop in range(0, self.fio_loop, 1):
                    fun_test.log("Running loop {} of {}".format((loop+1), self.fio_loop))
                    command_result = {}
                    initial_lsv_stats[combo][mode] = {}
                    storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                 "VOL_TYPE_BLK_LSV",
                                                                 self.lsv_uuid,
                                                                 "stats")
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial LSV stats of DUT")
                    initial_lsv_stats[combo][mode] = command_result["data"]
                    fun_test.log("LSV Stats at the beginning of the test:")
                    fun_test.log(initial_lsv_stats[combo][mode])

                    initial_crypto_stats[combo][mode] = {}
                    command_result = self.storage_controller.peek(crypto_props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial crypto stats of DUT")
                    initial_crypto_stats[combo][mode] = command_result["data"]
                    if initial_crypto_stats[combo][mode] is None:
                        initial_crypto_stats[combo][mode] = 0
                    fun_test.log("Crypto Stats at the beginning of the test:")
                    fun_test.log(initial_crypto_stats[combo][mode])

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
                            fun_test.log("FIO Command Output:")
                            fun_test.log(fio_output[combo][mode])
                        else:
                            fio_output[combo][mode] = {}
                            fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                 rw=mode,
                                                                                 bs=fio_block_size,
                                                                                 iodepth=fio_iodepth,
                                                                                 nsid=self.ns_id,
                                                                                 **self.fio_cmd_args)
                            fun_test.log("FIO Command Output:")
                            fun_test.log(fio_output[combo][mode])
                    else:
                        fun_test.log("Running fio test is threaded mode...")
                        thread_id = {}
                        wait_time = 0
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
                                fun_test.sleep("Fio threadzz", seconds=1)
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
                                    fun_test.sleep("Waiting for fio to exit...sleeping 10 secs", seconds=10)

                            fun_test.log("Timer expired, killing fio...")
                            self.linux_host.command("for i in `pgrep fio`;do kill -9 $i;done")

                            fun_test.log(command_result)
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

                    final_lsv_stats[combo][mode] = {}
                    storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                 "volumes",
                                                                 "VOL_TYPE_BLK_LSV",
                                                                 self.lsv_uuid,
                                                                 "stats")
                    command_result = {}
                    final_lsv_stats[combo][mode] = {}
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Final LSV stats on DUT")
                    final_lsv_stats[combo][mode] = command_result["data"]
                    fun_test.log("LSV Stats at the end of the test:")
                    fun_test.log(final_lsv_stats[combo][mode])

                    final_crypto_stats[combo][mode] = {}
                    command_result = self.storage_controller.peek(crypto_props_tree)
                    fun_test.simple_assert(command_result["status"], "Final crypto stats on DUT")
                    final_crypto_stats[combo][mode] = command_result["data"]
                    fun_test.log("Volume Crypto at the end of the test:")
                    fun_test.log(final_crypto_stats[combo][mode])

                    # Calculate the crypto stats diff
                    diff_crypto_stats[combo][mode] = {}
                    diff_crypto_stats[combo][mode] = final_crypto_stats[combo][mode] - initial_crypto_stats[combo][mode]
                    fun_test.log("Difference of Crypto stats before and after the test:")
                    fun_test.log(diff_crypto_stats[combo][mode])

                    diff_lsv_stats[combo][mode] = {}
                    total_diff_stats = 0
                    for fkey, fvalue in final_lsv_stats[combo][mode].items():
                        # Not going to calculate the difference for the value stats which are not in the expected
                        # volume dictionary and also for the fault_injection attribute
                        if fkey not in expected_lsv_stats[mode] or fkey == "fault_injection":
                            diff_lsv_stats[combo][mode][fkey] = fvalue
                            continue
                        if fkey in final_lsv_stats[combo][mode]:
                            ivalue = initial_lsv_stats[combo][mode][fkey]
                            diff_lsv_stats[combo][mode][fkey] = fvalue - ivalue
                            total_diff_stats += diff_lsv_stats[combo][mode][fkey]
                    fun_test.log("Difference of LSV stats before and after the test:")
                    fun_test.log(diff_lsv_stats[combo][mode])

                    # Calculate if diff of crypto and LSV stats is equal
                    if diff_crypto_stats[combo][mode] == total_diff_stats:
                        fun_test.add_checkpoint("Crypto count for the block size & IO depth combo {}".format(combo),
                                                "PASSED",
                                                total_diff_stats,
                                                diff_crypto_stats[combo][mode])
                    else:
                        fun_test.add_checkpoint("Crypto count for the block size & IO depth combo {}".format(combo),
                                                "FAILED",
                                                total_diff_stats,
                                                diff_crypto_stats[combo][mode])
                        fun_test.critical("Crypto stats don't match LSV stats")

                    for ekey, evalue in expected_lsv_stats[mode].items():
                        if ekey in diff_lsv_stats[combo][mode]:
                            actual = diff_lsv_stats[combo][mode][ekey]
                            if actual != evalue:
                                internal_result[combo][mode] = False
                                fun_test.add_checkpoint(
                                    "{} check for the {} test for the block size & IO depth combo "
                                    "{}".format(ekey, mode, combo), "FAILED", evalue, actual)
                                fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                                  format(ekey, actual, evalue))
                            else:
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth"
                                                        "combo {}".format(ekey, mode, combo), "PASSED", evalue,
                                                        actual)
                                fun_test.log("Final {} value {} is equal to the expected value {}".
                                             format(ekey, actual, evalue))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in volume stats".format(ekey))

                    # TODO : Check uncompress stats once SWOS-3737 is fixed
                    if self.compress:
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                     "volumes",
                                                                     "VOL_TYPE_BLK_LSV",
                                                                     self.lsv_uuid,
                                                                     "compression")
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree)
                        compression_stats = command_result["data"]
                        for ckey, cvalue in compression_stats.items():
                            if ckey == "compress_reqs":
                                compress_reqs = cvalue
                            elif ckey == "compress_done":
                                compress_done = cvalue
                            elif ckey == "compress_fails":
                                compress_fails = cvalue
                            elif ckey == "uncompress_fails":
                                uncompress_fails = cvalue
                        # fun_test.simple_assert(expression=compress_reqs == compress_done,
                        #                       message="Compression reqs & ops done")
                        fun_test.simple_assert(expression=compress_fails == uncompress_fails == 0,
                                               message="Compression failures")
                        fun_test.log(command_result["data"])

        # Get total write/read stats from the ndata BLT
        blt_count = fun_test.shared_variables["blt_count"] - self.nparity
        self.total_blt_ops = 0
        for x in range(1, blt_count, 1):
            command_result = {}
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                         "volumes",
                                                         "VOL_TYPE_BLK_LOCAL_THIN",
                                                         self.blt_uuid[x],
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            blt_vol_ops = command_result["data"]
            for bkey, bvalue in blt_vol_ops.items():
                if bkey == "num_writes":
                    self.total_blt_ops += bvalue
                elif bkey == "num_reads":
                    self.total_blt_ops += bvalue

        fun_test.log("Total ndata BLT ops is {}".format(self.total_blt_ops))

        # The total LSV write/read should match the total crypto operations.
        command_result = {}
        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                     "volumes",
                                                     "VOL_TYPE_BLK_LSV",
                                                     self.lsv_uuid,
                                                     "stats")
        command_result = self.storage_controller.peek(storage_props_tree)
        total_lsv_ops = command_result["data"]
        for tkey, tvalue in total_lsv_ops.items():
            if tkey == "num_writes":
                fun_test.shared_variables["total_lsv_ops"] += tvalue
            elif tkey == "num_reads":
                fun_test.shared_variables["total_lsv_ops"] += tvalue

        fun_test.log("Total LSV ops is {}".format(fun_test.shared_variables["total_lsv_ops"]))

        command_result = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        self.total_crypto_ops = command_result["data"]

        fun_test.log("The total crypto ops is {}". format(self.total_crypto_ops))

        if self.total_crypto_ops == fun_test.shared_variables["total_lsv_ops"]:
            fun_test.add_checkpoint("The total crypto operations and lsv operations",
                                    "PASSED",
                                    self.total_crypto_ops,
                                    fun_test.shared_variables["total_lsv_ops"])
        else:
            fun_test.add_checkpoint("The total crypto operations and lsv operations",
                                    "FAILED",
                                    self.total_crypto_ops,
                                    fun_test.shared_variables["total_lsv_ops"])
            fun_test.simple_assert(False, "Crypto ops don't match")

        fun_test.sleep(message="Sleeping before collecting final stats", seconds=5)
        # Check if all crypto stats match, but not using as sometimes the output is skewed
        # final_crypto_counts = {}
        # crypto_props_tree = "{}/{}/{}".format("stats", "wus", "counts")
        # command_result = {}
        # command_result = self.storage_controller.peek(crypto_props_tree)
        # final_crypto_counts = command_result["data"]
        for filter_param in self.filter_params:
            if filter_param != "vol_encrypt_filter_added" and filter_param != "vol_decrypt_filter_added":
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = {}
                command_result = self.storage_controller.peek(crypto_props_tree)
                if filter_param == "cryptofilter_create":
                    cryptofilter_create = command_result["data"]
                if filter_param != "vol_filter_create_done":
                    filter_result = command_result["data"]
                    fun_test.simple_assert(
                        expression=filter_result == fun_test.shared_variables["crypto_filter_count"],
                        message="Filter {} doesn't match".format(filter_param))
                else:
                    vol_filter_create_done = command_result["data"]
            elif filter_param == "vol_encrypt_filter_added":
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = {}
                command_result = self.storage_controller.peek(crypto_props_tree)
                encrypt_filter_count = command_result["data"]
            elif filter_param == "vol_decrypt_filter_added":
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)
                command_result = {}
                command_result = self.storage_controller.peek(crypto_props_tree)
                decrypt_filter_count = command_result["data"]

        total_crypto_filter = encrypt_filter_count + decrypt_filter_count
        if total_crypto_filter == cryptofilter_create:
            fun_test.add_checkpoint("Total Crypto filter count",
                                    "PASSED",
                                    cryptofilter_create,
                                    total_crypto_filter)
        else:
            fun_test.add_checkpoint("Total Crypto filter count",
                                    "FAILED",
                                    cryptofilter_create,
                                    total_crypto_filter)

        total_filter_count = total_crypto_filter + fun_test.shared_variables["compress_filter_count"]
        if total_filter_count == vol_filter_create_done:
            fun_test.add_checkpoint("Total filter count",
                                    "PASSED",
                                    vol_filter_create_done,
                                    total_filter_count)
        else:
            fun_test.add_checkpoint("Total filter count",
                                    "FAILED",
                                    vol_filter_create_done,
                                    total_filter_count)
            
        for crypto_ops_param in self.crypto_ops_params:
            crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", crypto_ops_param)
            command_result = {}
            command_result = self.storage_controller.peek(crypto_props_tree)
            final_crypto_counts = command_result["data"]
            if final_crypto_counts != self.total_crypto_ops:
                fun_test.add_checkpoint("{} parameter match cryptofilter_aes_xts?".format(crypto_ops_param),
                                        "FAILED",
                                        self.total_crypto_ops,
                                        final_crypto_counts)

        command_result = {}
        final_crypto_cluster_stats = {}
        command_result = self.storage_controller.peek(crypto_cluster_props_tree)
        final_crypto_cluster_stats = command_result["data"]

        crypto_dict = {}
        crypto_ops = 0
        xts_ops = 0
        for key, value in final_crypto_cluster_stats.items():
            if value != {}:
                crypto_dict = value
                xts_dict = {}
                for ckey, cvalue in crypto_dict.items():
                    if ckey == "AES_XTS":
                        xts_dict = cvalue
                        for xkey, xvalue in xts_dict.items():
                            if xkey == "num_ops":
                                xts_ops = xvalue
                                crypto_ops += xts_ops
                                fun_test.log("Crypto operations on {} is {}".format(key, xts_ops))

        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):

        if not self.blt_creation_fail:
            if self.traffic_parallel:
                self.attach_count = self.parallel_count + 1
                for x in range(1, self.attach_count, 1):
                    command_result = {}
                    command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                                  uuid=self.lsv_uuid,
                                                                                  remote_ip=self.linux_host.internal_ip)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detach LSV {}".format(x))

            else:
                command_result = {}
                command_result = self.storage_controller.volume_detach_remote(ns_id=self.ns_id,
                                                                              uuid=self.lsv_uuid,
                                                                              remote_ip=self.linux_host.internal_ip)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Detach LSV")

            command_result = {}
            command_result = self.storage_controller.delete_volume(capacity=self.lsv_capacity,
                                                                   block_size=self.lsv_blocksize,
                                                                   name="lsv1",
                                                                   uuid=self.lsv_uuid,
                                                                   type="VOL_TYPE_BLK_LSV")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleted LSV")

            command_result = {}
            command_result = self.storage_controller.delete_volume(capacity=self.jvol_details["capacity"],
                                                                   block_size=self.jvol_details["block_size"],
                                                                   name="jvol1",
                                                                   uuid=self.jvol_uuid,
                                                                   type="VOL_TYPE_BLK_NV_MEMORY")

            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleted Journal")

            command_result = {}
            command_result = self.storage_controller.delete_volume(capacity=self.ec_capacity,
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="ec_vol1",
                                                                   uuid=self.ec_uuid,
                                                                   type="VOL_TYPE_BLK_EC")

            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleted EC Vol")

            for x in range(1, fun_test.shared_variables["blt_count"], 1):
                command_result = {}
                command_result = self.storage_controller.delete_volume(capacity=self.blt_capacity,
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(x),
                                                                       uuid=self.blt_uuid[x],
                                                                       type="VOL_TYPE_BLK_LOCAL_THIN")
                fun_test.log(command_result)
                if command_result["status"]:
                    self.blt_delete_count += 1
                else:
                    fun_test.test_assert(not command_result["status"], "Deleting BLT {} on DUT".format(x))

            if self.blt_delete_count == self.blt_count:
                fun_test.add_checkpoint("Total BLT count {} & deleted BLT count {}".
                                        format(self.blt_count, self.blt_delete_count),
                                        "PASSED",
                                        self.blt_count,
                                        self.blt_delete_count)
                fun_test.simple_assert(True, "Deleted all BLT")
        fun_test.shared_variables["ec"]["setup_created"] = False

        # TODO code this check after SWOS-3597 is fixed
        # Cleanup should not have any traces of volumes left
        command_result = {}
        storage_props_tree = "{}/{}".format("storage", "volumes")
        command_result = self.storage_controller.peek(storage_props_tree)
        if command_result["status"]:
            fun_test.test_assert(command_result["status"], "Cleanup traces of volume")


class ECKey256(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create an EC with 256 bit key and run FIO with different RW pattern, block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey256, self).setup()

    def run(self):
        super(ECKey256, self).run()

    def cleanup(self):
        super(ECKey256, self).cleanup()


class ECKey256RW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create an EC with 256 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey256RW, self).setup()

    def run(self):
        super(ECKey256RW, self).run()

    def cleanup(self):
        super(ECKey256RW, self).cleanup()


class ECKey256RandRW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create an EC with 256 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using 256 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey256RandRW, self).setup()

    def run(self):
        super(ECKey256RandRW, self).run()

    def cleanup(self):
        super(ECKey256RandRW, self).cleanup()


class ECKey512(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create an EC with 512 bit key and run FIO with different RW pattern, block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey512, self).setup()

    def run(self):
        super(ECKey512, self).run()

    def cleanup(self):
        super(ECKey512, self).cleanup()


class ECKey512RW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Create an EC with 512 bit key and run FIO RW pattern with different block size"
                                      " & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey512RW, self).setup()

    def run(self):
        super(ECKey512RW, self).run()

    def cleanup(self):
        super(ECKey512RW, self).cleanup()


class ECKey512RandRW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create an EC with 512 bit key and run FIO RandRW pattern with different block "
                                      "size & depth",
                              steps='''
                              1. Create a lsv with encryption using 512 bit key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECKey512RandRW, self).setup()

    def run(self):
        super(ECKey512RandRW, self).run()

    def cleanup(self):
        super(ECKey512RandRW, self).cleanup()


class ECEncCompress(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create an EC with random key & compression and run diff FIO RW pattern with "
                                      "different block size & depth & deadbeef data pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncCompress, self).setup()

    def run(self):
        super(ECEncCompress, self).run()

    def cleanup(self):
        super(ECEncCompress, self).cleanup()


class ECEncCompressRW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Create an EC with random key & compression and run FIO RW pattern with"
                                      " different block size & depth & deadbeef data pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncCompressRW, self).setup()

    def run(self):
        super(ECEncCompressRW, self).run()

    def cleanup(self):
        super(ECEncCompressRW, self).cleanup()


class ECEncCompressRandRW(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Create an EC with random key & compression and run FIO RandRW pattern"
                                      " with different block size & depth & deadbeef data pattern",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncCompressRandRW, self).setup()

    def run(self):
        super(ECEncCompressRandRW, self).run()

    def cleanup(self):
        super(ECEncCompressRandRW, self).cleanup()


class ECEncDeadBeef(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Create an EC with random key and run diff FIO RW pattern with different block "
                                      "size & depth & deadbeef pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncDeadBeef, self).setup()

    def run(self):
        super(ECEncDeadBeef, self).run()

    def cleanup(self):
        super(ECEncDeadBeef, self).cleanup()


class ECEncZeroPattern(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Create an EC with random key and run diff FIO RW pattern with different block "
                                      "size & depth & 0x000000000 string pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncZeroPattern, self).setup()

    def run(self):
        super(ECEncZeroPattern, self).run()

    def cleanup(self):
        super(ECEncZeroPattern, self).cleanup()


class ECEncZeroHPattern(ECCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="Create an EC with random key and run diff FIO RW pattern with different block "
                                      "size & depth & 0x000000000 hex pattern in parallel",
                              steps='''
                              1. Create a lsv with encryption using random key on dut.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic.
        ''')

    def setup(self):
        super(ECEncZeroHPattern, self).setup()

    def run(self):
        super(ECEncZeroHPattern, self).run()

    def cleanup(self):
        super(ECEncZeroHPattern, self).cleanup()


if __name__ == "__main__":
    ecscript = ECCryptoVolumeScript()
    ecscript.add_test_case(ECKey256())
    ecscript.add_test_case(ECKey256RW())
    ecscript.add_test_case(ECKey256RandRW())
    ecscript.add_test_case(ECKey512())
    ecscript.add_test_case(ECKey512RW())
    ecscript.add_test_case(ECKey512RandRW())
    ecscript.add_test_case(ECEncCompress())
    ecscript.add_test_case(ECEncCompressRW())
    ecscript.add_test_case(ECEncCompressRandRW())
    ecscript.add_test_case(ECEncDeadBeef())
    ecscript.add_test_case(ECEncZeroPattern())
    ecscript.add_test_case(ECEncZeroHPattern())

    ecscript.run()
