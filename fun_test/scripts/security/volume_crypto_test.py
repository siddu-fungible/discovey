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
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of block size and IO depth combo
        if 'fio_bs_iodepth' not in testcase_dict[testcase] or not testcase_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_file))
        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut_instance, "Retrieved dut instance 0")

        self.linux_host = self.topology.get_tg_instance(tg_index=0)

        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)

        key256_count = 0
        key512_count = 0

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
            encrypt_consec = 0

            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                self.thin_uuid[x] = utils.generate_uuid()
                if self.key_size == "Auto":
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

                if self.volume_details["block_size"] == "Auto":
                    bs_auto = True
                    vol_bs_range = self.volume_details["block_size_range"]
                    self.block_size[x] = random.choice(vol_bs_range)
                    self.volume_details["block_size"] = self.block_size[x]

                if self.volume_details["capacity"] == "Auto":
                    capacity_auto = True
                    vol_cap_range = self.volume_details["capacity_range"]
                    self.vol_capacity[x] = random.choice(vol_cap_range)
                    self.volume_details["capacity"] = self.vol_capacity[x]
                    check_cap = self.volume_details["capacity"] % self.volume_details["block_size"]
                    fun_test.test_assert(expression=check_cap == 0,
                                         message="Capacity is a multiple of block size.")

                if self.volume_details["encrypt"] == "enable":
                    self.volume_details["encrypt"] = True
                    self.encrypted_vol[x] = self.thin_uuid[x]
                elif self.volume_details["encrypt"] == "disable":
                    encrypt_consec = 1
                    self.volume_details["encrypt"] = False
                elif self.volume_details["encrypt"] == "consecutive" and encrypt_consec == 0:
                    encrypt_consec = 1
                    self.volume_details["encrypt"] = True
                    self.encrypted_vol[x] = self.thin_uuid[x]

                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                       capacity=self.volume_details["capacity"],
                                                                       block_size=self.volume_details["block_size"],
                                                                       name="think-block" + str(x),
                                                                       uuid=self.thin_uuid[x],
                                                                       encrypt=self.volume_details["encrypt"],
                                                                       key=self.xts_key,
                                                                       xtweak=self.xts_tweak,
                                                                       command_duration=self.command_timeout)

                if bs_auto:
                    self.volume_details["block_size"] = "Auto"
                if capacity_auto:
                    self.volume_details["capacity"] = "Auto"
                if encrypt_consec == 1:
                    encrypt_consec = 0
                    self.volume_details["encrypt"] = False
                else:
                    self.volume_details["encrypt"] = "consecutive"

                if (self.key_size == 32 or self.key_size == 64 or self.key_size == "Auto") and self.xtweak_size == 8:
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

                    command_result = {}
                    command_result = self.storage_controller.volume_attach_remote(ns_id=x,
                                                                                  uuid=self.thin_uuid[x],
                                                                                  remote_ip=self.linux_host.internal_ip,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")

                    fun_test.shared_variables["blt"]["setup_created"] = True
                    # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller

                else:
                    if command_result["status"]:
                        fun_test.test_assert(command_result["status"],
                                             message="Volume creation should have failed.")
                    else:
                        fun_test.test_assert(not command_result["status"],
                                             message="Volume creation failed as expected.")
            if self.key_size == "Auto":
                fun_test.log("Total volumes with 256 bit key: {}".format(key256_count))
                fun_test.log("Total volumes with 512 bit key: {}".format(key512_count))

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
        diff_volume_stats = {}
        initial_volume_stats = {}
        final_volume_stats = {}

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
            diff_volume_stats[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            if not self.traffic_parallel:

                for mode in self.fio_modes:

                    tmp = combo.split(',')
                    fio_block_size = tmp[0].strip('() ') + 'k'
                    fio_iodepth = tmp[1].strip('() ')
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True

                    fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                                 format(mode, fio_block_size, fio_iodepth))

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

                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    for loop in range(0, self.fio_loop, 1):
                        fun_test.log("Fio loop count: {}".format(loop))
                        if mode == "rw" or mode == "randrw":
                            for x in range(1, fun_test.shared_variables["volume_count"], 1):
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
                            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                                fio_output[combo][mode] = {}
                                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                     rw=mode,
                                                                                     bs=fio_block_size,
                                                                                     iodepth=fio_iodepth,
                                                                                     nsid=x,
                                                                                     **self.fio_cmd_args)
                                fun_test.log("FIO Command Output:")
                                fun_test.log(fio_output[combo][mode])

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

            else:
                fun_test.log("Running Fio tests is parallel.")
                for mode in self.fio_modes:
                    tmp = combo.split(',')
                    fio_block_size = tmp[0].strip('() ') + 'k'
                    fio_iodepth = tmp[1].strip('() ')
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True
                    fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                                 format(mode, fio_block_size, fio_iodepth))

                    command_result = {}
                    initial_volume_stats[combo][mode] = {}
                    for x in range(1, fun_test.shared_variables["volume_count"], 1):
                        initial_volume_stats[combo][mode][x] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     self.thin_uuid[x],
                                                                     "stats")
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
                        initial_volume_stats[combo][mode][x] = command_result["data"]
                        fun_test.log("Volume Stats at the beginning of the test:")
                        fun_test.log(initial_volume_stats[combo][mode][x])

                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    if mode == "rw" or mode == "randrw":
                        thread_id = {}
                        wait_time = 0
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            wait_time = fun_test.shared_variables["volume_count"] - x
                            fio_output[combo][mode] = {}
                            self.linux_host_inst[x] = self.linux_host.clone()
                            thread_id[x] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=self.linux_host_inst[x],
                                                                         destination_ip=destination_ip,
                                                                         rw=mode,
                                                                         rwmixread=30,
                                                                         bs=fio_block_size,
                                                                         iodepth=fio_iodepth,
                                                                         nsid=x,
                                                                         **self.fio_cmd_args)
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])

                    else:
                        thread_id = {}
                        wait_time = 0
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            wait_time = fun_test.shared_variables["volume_count"] - x
                            print "Running thread after wait_time " + str(wait_time)
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
                            # Put sleep

                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            fun_test.log("")
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])
                    # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")

            final_volume_stats[combo][mode] = {}
            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                             "VOL_TYPE_BLK_LOCAL_THIN",
                                                             self.thin_uuid[x],
                                                             "stats")
                command_result = {}
                final_volume_stats[combo][mode][x] = {}
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
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
        final_volume_stats[combo][mode] = {}
        for key, value in self.encrypted_vol.items():
            final_volume_stats[combo][mode][key] = {}
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                         value,
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            final_volume_stats[combo][mode][key] = command_result["data"]
            for fkey, fvalue in final_volume_stats[combo][mode][key].items():
                if fkey == "num_writes":
                    total_crypto_writes = fvalue
                elif fkey == "num_reads":
                    total_crypto_reads = fvalue
                crypto_vol_ops = total_crypto_reads + total_crypto_writes
            fun_test.shared_variables["total_vol_crypto_ops"] += crypto_vol_ops

        print "The total crypto vol ops is " + str(fun_test.shared_variables["total_vol_crypto_ops"])

        # Getting the volume stats after the FIO test
        command_result = {}
        final_volume_stats[combo][mode] = {}
        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            final_volume_stats[combo][mode][x] = {}
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                         self.thin_uuid[x],
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
            final_volume_stats[combo][mode][x] = command_result["data"]
            fun_test.log("Volume Stats at the end of the test:")
            fun_test.log(final_volume_stats[combo][mode][x])

        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            for key, value in final_volume_stats[combo][mode][x].items():
                if key == "num_reads":
                    total_vol_reads = value
                elif key == "num_writes":
                    total_vol_writes = value
            volume_ops = total_vol_reads + total_vol_writes
            fun_test.shared_variables["total_volume_ops"] += volume_ops

        print "The total volume ops of all volumes is " + str(fun_test.shared_variables["total_volume_ops"])

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

        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            command_result = {}
            command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                          uuid=self.thin_uuid[x],
                                                                          remote_ip=self.linux_host.internal_ip)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detaching Volume from DUT Instance 0")
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
            fun_test.test_assert(command_result["status"], "Deleting Volume")

            if bs_auto:
                self.volume_details["block_size"] = "Auto"
            if capacity_auto:
                self.volume_details["capacity"] = "Auto"

        self.storage_controller.disconnect()
        fun_test.shared_variables["blt"]["setup_created"] = False
        # pass


class VolumeKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a volume with 256 bit key .",
                              steps='''
                              1. Create a local thin block volume with encryption using 256 bit in dut instances 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(VolumeKey256, self).setup()

    def run(self):
        super(VolumeKey256, self).run()
        # pass

    def cleanup(self):
        super(VolumeKey256, self).cleanup()


class VolumeKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Create a volume with 512 bit key .",
                              steps='''
                              1. Create a local thin block volume with encryption using 512 bit in dut instance 0.
                              2. Attach it to external linux/container.
                              3. Run FIO write traffic.
        ''')

    def setup(self):
        super(VolumeKey512, self).setup()

    def run(self):
        super(VolumeKey512, self).run()
        # pass

    def cleanup(self):
        super(VolumeKey512, self).cleanup()


class WrongKey(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Create a volume with wrong key.",
                              steps='''
                              1. Create a local thin block volume with encryption using a wrong length key.
        ''')

    def setup(self):
        super(WrongKey, self).setup()

    def run(self):
        # super(VolumeKey512, self).run()
        pass

    def cleanup(self):
        super(WrongKey, self).cleanup()


class WrongTweak(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create a volume with wrong tweak.",
                              steps='''
                              1. Create a local thin block volume with encryption using a wrong tweak key.
        ''')

    def setup(self):
        super(WrongTweak, self).setup()

    def run(self):
        # super(VolumeKey512, self).run()
        pass

    def cleanup(self):
        super(WrongTweak, self).cleanup()


class MultipleBltKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Create multiple volume with 256 bit key and run fio.",
                              steps='''
                              1. Create multiple local thin block volume with encryption.
                              2. Attach it to external linux/container.
                              3. Run FIO on all volumes.
        ''')

    def setup(self):
        super(MultipleBltKey256, self).setup()

    def run(self):
        super(MultipleBltKey256, self).run()

    def cleanup(self):
        super(MultipleBltKey256, self).cleanup()


class MultipleBltKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create multiple volume with 512 bit key and run fio.",
                              steps='''
                              1. Create multiple local thin block volume with encryption.
                              2. Attach it to external linux/container.
                              3. Run FIO on all volumes.
        ''')

    def setup(self):
        super(MultipleBltKey512, self).setup()

    def run(self):
        super(MultipleBltKey512, self).run()

    def cleanup(self):
        super(MultipleBltKey512, self).cleanup()


class CreateDelete256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create/Delete multiple volumes with 256 bit key.",
                              steps='''
                              1. Create multiple local thin block volume with encryption.
                              2. Attach it to external linux/container.
                              3. Detach and Delete them.
        ''')

    def setup(self):
        super(CreateDelete256, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(CreateDelete256, self).cleanup()


class CreateDelete512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Create/Delete multiple volumes with 512 bit key.",
                              steps='''
                              1. Create multiple local thin block volume with encryption.
                              2. Attach it to external linux/container.
                              3. Detach and Delete them.
        ''')

    def setup(self):
        super(CreateDelete512, self).setup()

    def run(self):
        pass

    def cleanup(self):
        super(CreateDelete512, self).cleanup()


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(VolumeKey256())
#    bltscript.add_test_case(VolumeKey512())
#    bltscript.add_test_case(WrongKey())
#    bltscript.add_test_case(WrongTweak())
#    bltscript.add_test_case(MultipleBltKey256())
#    bltscript.add_test_case(MultipleBltKey512())
#    bltscript.add_test_case(CreateDelete256())
#    bltscript.add_test_case(CreateDelete512())
    bltscript.run()
