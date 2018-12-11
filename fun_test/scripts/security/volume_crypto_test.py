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


class BLTCryptoVolumeScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        # topology_obj_helper.save(file_name="/tmp/pickle.pkl")
        # topology = topology_obj_helper.load(file_name="/tmp/pickle.pkl")
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology
        # We have declared this here since when we remove volume, the counters are from zero but crypto
        # counters are not from zero.
        fun_test.shared_variables["total_volume_ops"] = 0
        fun_test.shared_variables["vol_encrypt_filter"] = 0
        fun_test.shared_variables["vol_decrypt_filter"] = 0
        fun_test.shared_variables["total_vol_crypto_ops"] = 0

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
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
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase.".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of block size and IO depth combo
        if 'fio_bs_iodepth' not in testcase_dict[testcase] or not testcase_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file.".format(testcase, testcase_file))
        fun_test.test_assert(benchmark_parsing, "Parsing testcase json file for this {} testcase.".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}.".
                     format(testcase, self.fio_bs_iodepth))

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file.".format(testcase, testcase_dict))

        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut_instance, "Retrieved dut instance 0")

        self.linux_host = self.topology.get_tg_instance(tg_index=0)

        self.linux_host_inst = {}
        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)
        key256_count = 0
        key512_count = 0
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0
        self.correct_key_tweak = None
        self.blt_creation_fail = None

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            # Configuring Local thin block volume
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT Instance 0")

            command_result = {}
            command_result = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip,
                                                            command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on Dut Instance 0".
                                 format(self.dut_instance.data_plane_ip))

            command_result = {}
            fun_test.shared_variables["volume_count"] = self.volume_count + 1
            self.thin_uuid = {}
            self.block_size = {}
            self.vol_capacity = {}
            self.encrypted_vol = {}
            bs_auto = None
            capacity_auto = None

            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                self.thin_uuid[x] = utils.generate_uuid()
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

                if self.volume_details["block_size"] == "Auto":
                    bs_auto = True
                    self.block_size[x] = random.choice(self.volume_details["block_size_range"])
                    self.volume_details["block_size"] = self.block_size[x]

                if self.volume_details["capacity"] == "Auto":
                    capacity_auto = True
                    self.vol_capacity[x] = random.choice(self.volume_details["capacity_range"])
                    self.volume_details["capacity"] = self.vol_capacity[x]
                    check_cap = self.volume_details["capacity"] % self.volume_details["block_size"]
                    fun_test.test_assert(expression=check_cap == 0,
                                         message="Capacity is a multiple of block size.")

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
                                                                       name="think-block" + str(x),
                                                                       uuid=self.thin_uuid[x],
                                                                       encrypt=self.vol_encrypt,
                                                                       key=self.xts_key,
                                                                       xtweak=self.xts_tweak,
                                                                       command_duration=self.command_timeout)

                if bs_auto:
                    self.volume_details["block_size"] = "Auto"
                if capacity_auto:
                    self.volume_details["capacity"] = "Auto"

                if (self.key_size == 32 or self.key_size == 64 or self.key_size == "random" or
                    self.key_size == "alternate" or not self.vol_encrypt) and self.xtweak_size == 8:

                    self.correct_key_tweak = True

                    fun_test.log(command_result)
                    if command_result["status"]:
                        self.blt_create_count += 1
                    else:
                        fun_test.test_assert(command_result["status"], "Creation of BLT {} on DUT".format(x))

                    command_result = {}
                    command_result = self.storage_controller.volume_attach_remote(ns_id=x,
                                                                                  uuid=self.thin_uuid[x],
                                                                                  remote_ip=self.linux_host.internal_ip,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    if command_result["status"]:
                        self.blt_attach_count += 1
                    else:
                        fun_test.test_assert(command_result["status"],
                                             "Attaching of BLT {} on DUT".format(x))

                    fun_test.shared_variables["blt"]["setup_created"] = True
                    # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller

                elif self.vol_encrypt:
                    fun_test.test_assert(not command_result["status"],
                                         message="BLT creation should fail")
                    self.blt_creation_fail = True
                else:
                    fun_test.test_assert(command_result["status"], "BLT creation with encryption disabled")

            if self.key_size == "random" or self.key_size == "alternate":
                fun_test.log("Total BLT with 256 bit key: {}".format(key256_count))
                fun_test.log("Total BLT with 512 bit key: {}".format(key512_count))

            if self.blt_create_count == self.volume_count:
                fun_test.add_checkpoint("Creation of {} BLT succeeded".format(self.volume_count),
                                        "PASSED",
                                        self.volume_count,
                                        self.blt_create_count)
                fun_test.test_assert(True,
                                     "Creation of {} BLT from DUT instance 0 succeeded".format(self.blt_create_count))
            else:
                fun_test.add_checkpoint("Creation of BLT".format(self.volume_count),
                                        "FAILED",
                                        self.volume_count,
                                        self.blt_create_count)

            if self.blt_attach_count == self.volume_count:
                fun_test.add_checkpoint("Attaching of {} BLT succeeded".format(self.volume_count),
                                        "PASSED",
                                        self.volume_count,
                                        self.blt_attach_count)
                fun_test.test_assert(True,
                                     "Attaching of {} BLT from DUT instance 0 succeeded".format(self.blt_attach_count))
            else:
                fun_test.add_checkpoint("Attach of BLT".format(self),
                                        "FAILED",
                                        self.volume_count,
                                        self.blt_attach_count)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        total_vol_reads = 0
        total_vol_writes = 0
        total_crypto_writes = 0
        total_crypto_reads = 0
        crypto_vol_ops = 0

        crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", "cryptofilter_aes_xts")

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}
        diff_volume_stats = {}
        diff_crypto_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}
        final_encrypted_vol_stats = {}

        command_result = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        fun_test.log("Crypto Stats at the beginning of the test:")
        fun_test.log(command_result["data"])

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            final_volume_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}
            diff_volume_stats[combo] = {}
            diff_crypto_stats[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}
            final_encrypted_vol_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

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
                    initial_volume_stats[combo][mode] = {}
                    for x in range(1, fun_test.shared_variables["volume_count"], 1):
                        initial_volume_stats[combo][mode][x] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
                        initial_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("Volume Stats at the beginning of the test:")
                        fun_test.log(initial_volume_stats[combo][mode][x])

                    if not self.traffic_parallel:
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            if mode == "rw" or mode == "randrw":
                                fio_output[combo][mode] = {}
                                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                     rw=mode,
                                                                                     bs=fio_block_size,
                                                                                     iodepth=fio_iodepth,
                                                                                     rwmixread=self.fio_rwmixread,
                                                                                     nsid=x,
                                                                                     **self.fio_cmd_args)
                                fun_test.log("FIO Command Output:")
                                fun_test.log(fio_output[combo][mode])
                            else:
                                fio_output[combo][mode] = {}
                                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                     rw=mode,
                                                                                     bs=fio_block_size,
                                                                                     iodepth=fio_iodepth,
                                                                                     nsid=x,
                                                                                     **self.fio_cmd_args)
                                fun_test.log("FIO Command Output:")
                                fun_test.log(fio_output[combo][mode])
                    else:
                        fun_test.log("Running fio test is threaded mode...")
                        thread_id = {}
                        wait_time = 0
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            if mode == "rw" or mode == "randrw":
                                wait_time = fun_test.shared_variables["volume_count"] - x
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
                                wait_time = fun_test.shared_variables["volume_count"] - x
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
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            fun_test.log("Joining thread {}".format(x))
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])

                        if self.linux_host.command("pgrep fio"):
                            timer_kill = FunTimer(max_time=self.fio_cmd_args["timeout"] * 2)
                            while not timer_kill.is_expired():
                                if not self.linux_host.command("pgrep fio"):
                                    break
                                else:
                                    fun_test.sleep("Waiting for fio to exit...sleeping 20 secs", seconds=20)

                            fun_test.log("Timer expired, killing fio...")
                            self.linux_host.command("for i in `pgrep fio`;do kill -9 $i;done")

                    if self.detach_vol:

                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            command_result = {}
                            command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                                          uuid=self.thin_uuid[x],
                                                                                          remote_ip=self.linux_host.internal_ip)
                            fun_test.log(command_result)

                            command_result = {}
                            command_result = self.storage_controller.volume_attach_remote(ns_id=x,
                                                                                          uuid=self.thin_uuid[x],
                                                                                          remote_ip=self.linux_host.internal_ip,
                                                                                          command_duration=self.command_timeout)

                            fun_test.log(command_result)
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

                    final_volume_stats[combo][mode] = {}
                    for x in range(1, fun_test.shared_variables["volume_count"], 1):
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                     "volumes",
                                                                     "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = {}
                        final_volume_stats[combo][mode][x] = {}
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance 0")
                        final_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("Volume Stats at the end of the test:")
                        fun_test.log(final_volume_stats[combo][mode][x])

                    diff_volume_stats[combo][mode] = {}
                    for x in range(1, fun_test.shared_variables["volume_count"], 1):
                        diff_volume_stats[combo][mode][x] = {}
                        for fkey, fvalue in final_volume_stats[combo][mode][x].items():
                            # Not going to calculate the difference for the value stats which are not in the expected volume
                            # dictionary and also for the fault_injection attribute
                            if fkey not in expected_volume_stats[mode] or fkey == "fault_injection":
                                diff_volume_stats[combo][mode][x][fkey] = fvalue
                                continue
                            if fkey in initial_volume_stats[combo][mode][x]:
                                ivalue = initial_volume_stats[combo][mode][x][fkey]
                                diff_volume_stats[combo][mode][x][fkey] = fvalue - ivalue
                        fun_test.log("Difference of volume stats before and after the test:")
                        fun_test.log(diff_volume_stats[combo][mode][x])

                    for x in range(1, fun_test.shared_variables["volume_count"], 1):
                        for ekey, evalue in expected_volume_stats[mode].items():
                            if ekey in diff_volume_stats[combo][mode][x]:
                                actual = diff_volume_stats[combo][mode][x][ekey]
                                if actual != evalue:
                                    internal_result[combo][mode] = False
                                    fun_test.add_checkpoint(
                                        "{} check for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, mode, combo), "FAILED", evalue, actual)
                                    fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                                      format(ekey, actual, evalue))
                                else:
                                    fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                            "{}".format(ekey, mode, combo), "PASSED", evalue, actual)
                                    fun_test.log("Final {} value {} is equal to the expected value {}".
                                                 format(ekey, actual, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.critical("{} is not found in volume stats".format(ekey))

        command_result = {}
        final_encrypted_vol_stats[combo][mode] = {}
        for key, value in self.encrypted_vol.items():
            final_encrypted_vol_stats[combo][mode][key] = {}
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                         "volumes",
                                                         "VOL_TYPE_BLK_LOCAL_THIN",
                                                         value,
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            final_encrypted_vol_stats[combo][mode][key] = command_result["data"]
            for fkey, fvalue in final_encrypted_vol_stats[combo][mode][key].items():
                if fkey == "num_writes":
                    total_crypto_writes = fvalue
                elif fkey == "num_reads":
                    total_crypto_reads = fvalue
                crypto_vol_ops = total_crypto_reads + total_crypto_writes
            fun_test.shared_variables["total_vol_crypto_ops"] += crypto_vol_ops

        print "The total crypto vol ops is " + str(fun_test.shared_variables["total_vol_crypto_ops"])

        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            for key, value in final_volume_stats[combo][mode][x].items():
                if key == "num_reads":
                    total_vol_reads = value
                elif key == "num_writes":
                    total_vol_writes = value
            volume_ops = total_vol_reads + total_vol_writes
            fun_test.shared_variables["total_volume_ops"] += volume_ops

        print "Final volume ops(R+W) of all volumes is " + str(fun_test.shared_variables["total_volume_ops"])

        command_result = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        fun_test.shared_variables["total_crypto_ops"] = command_result["data"]

        print "The total crypto ops is " + str(fun_test.shared_variables["total_crypto_ops"])

        if fun_test.shared_variables["total_crypto_ops"] == fun_test.shared_variables["total_vol_crypto_ops"]:
            fun_test.add_checkpoint("The total crypto operations and encrypted volume operations match".
                                    format(self),
                                    "PASSED", fun_test.shared_variables["total_crypto_ops"],
                                    fun_test.shared_variables["total_vol_crypto_ops"])
        else:
            fun_test.add_checkpoint("The total crypto operations and encrypted volume operations doesn't match".
                                    format(self),
                                    "FAILED", fun_test.shared_variables["total_crypto_ops"],
                                    fun_test.shared_variables["total_vol_crypto_ops"])

        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        bs_auto = None
        capacity_auto = None

        if not self.blt_creation_fail:

            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                if self.correct_key_tweak:
                    command_result = {}
                    command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                                  uuid=self.thin_uuid[x],
                                                                                  remote_ip=self.linux_host.internal_ip)
                    fun_test.log(command_result)
                    if command_result["status"]:
                        self.blt_detach_count += 1
                    else:
                        fun_test.test_assert(command_result["status"], "Detaching of BLT {}".format(x))

            if self.volume_details["block_size"] == "Auto":
                bs_auto = True
                self.volume_details["block_size"] = self.block_size[x]

            if self.volume_details["capacity"] == "Auto":
                capacity_auto = True
                self.volume_details["capacity"] = self.vol_capacity[x]

            command_result = {}
            command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   name="thin-block" + str(x),
                                                                   uuid=self.thin_uuid[x],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.log(command_result)
            if command_result["status"]:
                self.blt_delete_count += 1
            else:
                fun_test.test_assert(not command_result["status"], "Deleting BLT {} on DUT".format(x))

            if bs_auto:
                self.volume_details["block_size"] = "Auto"
            if capacity_auto:
                    self.volume_details["capacity"] = "Auto"

            if self.blt_detach_count == self.volume_count:
                fun_test.add_checkpoint("Detach of {} BLT on DUT".format(self.volume_count),
                                        "PASSED",
                                        self.volume_count,
                                        self.blt_detach_count)
                fun_test.test_assert(True, "Detach of {} BLT succeeded".format(self.blt_detach_count))
            else:
                fun_test.add_checkpoint("Detach of BLT",
                                        "FAILED",
                                        self.volume_count,
                                        self.blt_detach_count)

            if self.blt_delete_count == self.volume_count:
                fun_test.add_checkpoint("Delete of {} BLT on DUT".format(self.volume_count),
                                        "PASSED",
                                        self.volume_count,
                                        self.blt_delete_count)
                fun_test.test_assert(True, "Delete of {} BLT succeeded.".format(self.blt_delete_count))
            else:
                fun_test.add_checkpoint("Delete of BLT",
                                        "FAILED",
                                        self.volume_count,
                                        self.blt_delete_count)

        self.storage_controller.disconnect()
        fun_test.shared_variables["blt"]["setup_created"] = False
        # pass


class BLTKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a volume with 256 bit key.",
                              steps='''
                              1. Create a local thin block volume with encryption using 256 bit in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey256, self).setup()

    def run(self):
        super(BLTKey256, self).run()
        # pass

    def cleanup(self):
        super(BLTKey256, self).cleanup()


class BLTKey256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create BLT's with encryption using 256 bit key & run RW test.",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey256RW, self).setup()

    def run(self):
        super(BLTKey256RW, self).run()
        # pass

    def cleanup(self):
        super(BLTKey256RW, self).cleanup()


class BLTKey256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create BLT's with encryption using 256 bit key & run RandRW test.",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey256RandRW, self).setup()

    def run(self):
        super(BLTKey256RandRW, self).run()
        # pass

    def cleanup(self):
        super(BLTKey256RandRW, self).cleanup()


class BLTKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create a volume with 512 bit key.",
                              steps='''
                              1. Create a local thin block volume with encryption using 512 bit in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey512, self).setup()

    def run(self):
        super(BLTKey512, self).run()
        # pass

    def cleanup(self):
        super(BLTKey512, self).cleanup()


class BLTKey512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Create BLT's with encryption using 512 bit key & run RW test.",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey512RW, self).setup()

    def run(self):
        super(BLTKey512RW, self).run()
        # pass

    def cleanup(self):
        super(BLTKey512RW, self).cleanup()


class BLTKey512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create BLT's with encryption using 512 bit key & run RandRW test.",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTKey512RandRW, self).setup()

    def run(self):
        super(BLTKey512RandRW, self).run()
        # pass

    def cleanup(self):
        super(BLTKey512RandRW, self).cleanup()


class MultipleBLT256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create 10 BLT's with encryption using 256 bit key & run test.",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT256, self).setup()

    def run(self):
        super(MultipleBLT256, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT256, self).cleanup()


class MultipleBLT256RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Create 10 BLT's with encryption using 256 bit key & run RW test.",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT256RW, self).setup()

    def run(self):
        super(MultipleBLT256RW, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT256RW, self).cleanup()


class MultipleBLT256RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Create 10 BLT's with encryption using 256 bit key & run RandRW test.",
                              steps='''
                              1. Create a BLT with encryption using 256 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT256RandRW, self).setup()

    def run(self):
        super(MultipleBLT256RandRW, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT256RandRW, self).cleanup()


class MultipleBLT512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Create 10 BLT's with encryption using 512 bit key & run test.",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT512, self).setup()

    def run(self):
        super(MultipleBLT512, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT512, self).cleanup()


class MultipleBLT512RW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Create 10 BLT's with encryption using 512 bit key & run RW test.",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT512RW, self).setup()

    def run(self):
        super(MultipleBLT512RW, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT512RW, self).cleanup()


class MultipleBLT512RandRW(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="Create 10 BLT's with encryption using 512 bit key & run RandRW test.",
                              steps='''
                              1. Create a BLT with encryption using 512 bit key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO traffic in parallel on all volumes.
        ''')

    def setup(self):
        super(MultipleBLT512RandRW, self).setup()

    def run(self):
        super(MultipleBLT512RandRW, self).run()
        # pass

    def cleanup(self):
        super(MultipleBLT512RandRW, self).cleanup()


class WrongKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=13,
                              summary="Create BLT's with wrong size key.",
                              steps='''
                              1. Create a BLT with encryption using unsupported key in dut instances 0.
        ''')

    def setup(self):
        super(WrongKey, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(WrongKey, self).cleanup()


class WrongTweak(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=14,
                              summary="Create BLT's with wrong size tweak.",
                              steps='''
                              1. Create a BLT with encryption using unsupported tweak in dut instances 0.
        ''')

    def setup(self):
        super(WrongTweak, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(WrongTweak, self).cleanup()


class BLTRandomKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=15,
                              summary="Create BLT's with encryption on BLT with random size key.",
                              steps='''
                              1. Create a BLT with encryption using random key in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(BLTRandomKey, self).setup()

    def run(self):
        super(BLTRandomKey, self).run()
        # pass

    def cleanup(self):
        super(BLTRandomKey, self).cleanup()


class CreateDelete256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=16,
                              summary="Create & delete 25 BLT's with encryption with 256 size key.",
                              steps='''
                              1. Create BLT's with encryption with 512 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def setup(self):
        super(CreateDelete256, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(CreateDelete256, self).cleanup()


class CreateDelete512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=17,
                              summary="Create & delete 25 BLT's with encryption with 512 size key.",
                              steps='''
                              1. Create BLT's with encryption with 512 size key.
                              2. Attach it to external linux/container.
                              3. Detach and delete the BLT.
        ''')

    def setup(self):
        super(CreateDelete512, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(CreateDelete512, self).cleanup()


class MultiVolRandKeyRandCap(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=18,
                              summary="Create 8 BLT with rand capacity & rand encryption key.",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth of 8 in parallel.
        ''')

    def setup(self):
        super(MultiVolRandKeyRandCap, self).setup()

    def run(self):
        super(MultiVolRandKeyRandCap, self).run()

    def cleanup(self):
        super(MultiVolRandKeyRandCap, self).cleanup()


class BLTFioDetach(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=19,
                              summary="Detach volume after running fio test",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth of 8 in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')

    def setup(self):
        super(BLTFioDetach, self).setup()

    def run(self):
        super(BLTFioDetach, self).run()

    def cleanup(self):
        super(BLTFioDetach, self).cleanup()


class BLTFioEncZeroPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=20,
                              summary="Encrypt BLT and run fio with pattern 0x000000000",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth of 8 in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')

    def setup(self):
        super(BLTFioEncZeroPattern, self).setup()

    def run(self):
        super(BLTFioEncZeroPattern, self).run()

    def cleanup(self):
        super(BLTFioEncZeroPattern, self).cleanup()


class BLTFioEncDeadBeefPattern(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=21,
                              summary="Encrypt BLT and run fio with deadbeef pattern",
                              steps='''
                              1. Create 8 BLT with rand capacity & rand encryption key.
                              2. Attach it to external linux/container.
                              3. Run Fio with different block size & IO depth of 8 in parallel.
                              4. After test is done remove and attach the BLT.
                              5. Start the fio test again.
        ''')

    def setup(self):
        super(BLTFioEncDeadBeefPattern, self).setup()

    def run(self):
        super(BLTFioEncDeadBeefPattern, self).run()

    def cleanup(self):
        super(BLTFioEncDeadBeefPattern, self).cleanup()


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(BLTKey256())
    bltscript.add_test_case(BLTKey256RW())
    bltscript.add_test_case(BLTKey256RandRW())
    bltscript.add_test_case(BLTKey512())
    bltscript.add_test_case(BLTKey512RW())
    bltscript.add_test_case(BLTKey512RandRW())
    bltscript.add_test_case(MultipleBLT256())
    bltscript.add_test_case(MultipleBLT256RW())
    bltscript.add_test_case(MultipleBLT256RandRW())
    bltscript.add_test_case(MultipleBLT512())
    bltscript.add_test_case(MultipleBLT512RW())
    bltscript.add_test_case(MultipleBLT512RandRW())
    bltscript.add_test_case(WrongKey())
    bltscript.add_test_case(WrongTweak())
    bltscript.add_test_case(BLTRandomKey())
    bltscript.add_test_case(CreateDelete256())
    bltscript.add_test_case(CreateDelete512())
    bltscript.add_test_case(MultiVolRandKeyRandCap())
    bltscript.add_test_case(BLTFioDetach())
    bltscript.add_test_case(BLTFioEncZeroPattern())
    bltscript.add_test_case(BLTFioEncDeadBeefPattern())

    bltscript.run()
