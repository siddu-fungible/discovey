from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from lib.fun.f1 import F1
import uuid


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


def generate_uuid(length=16):
    this_uuid = str(uuid.uuid4()).replace("-", "")[length:]
    return this_uuid


def generate_key(length=32):
    vol_key = os.urandom(length).encode('hex')
    return vol_key


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
            fun_test.shared_variables["vol_data"] = {}

            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                self.thin_uuid = generate_uuid()
                self.xts_key = generate_key(self.key_size)
                self.xts_tweak = generate_key(self.xtweak_size)
                self.vol_name = "thin-block"
                self.vol_name += str(x)

                fun_test.shared_variables["vol_data"][x] = {"name": self.vol_name, "uuid": self.thin_uuid}

                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                       capacity=self.volume_details["capacity"],
                                                                       block_size=self.volume_details["block_size"],
                                                                       name=fun_test.shared_variables["vol_data"]
                                                                       [x]["name"],
                                                                       uuid=fun_test.shared_variables["vol_data"]
                                                                       [x]["uuid"],
                                                                       encrypt=self.volume_details["encrypt"],
                                                                       key=self.xts_key,
                                                                       xtweak=self.xts_tweak,
                                                                       command_duration=self.command_timeout)

                if (self.key_size == 32 or self.key_size == 64) and self.xtweak_size == 8:
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

                    command_result = {}
                    command_result = self.storage_controller.volume_attach_remote(ns_id=x,
                                                                                  uuid=fun_test.shared_variables
                                                                                  ["vol_data"][x]["uuid"],
                                                                                  remote_ip=self.linux_host.internal_ip,
                                                                                  command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")

                    fun_test.shared_variables["blt"]["setup_created"] = True
                    # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller

                else:
                    if not command_result["status"]:
                        fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                                      message="Volume creation failed as expected.")
                    else:
                        fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                                      message="Volume creation should have failed.")

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        total_vol_reads = 0
        total_vol_writes = 0

        crypto_props_tree = "{}/{}/{}".format("stats", "wus", "counts")

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        final_volume_stats = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            final_volume_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}

            if not self.traffic_parallel:

                for mode in self.fio_modes:

                    tmp = combo.split(',')
                    fio_block_size = tmp[0].strip('() ') + 'k'
                    fio_iodepth = tmp[1].strip('() ')
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True

                    fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                                 format(mode, fio_block_size, fio_iodepth))

                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    if mode == "rw" or mode == "randrw":
                        for x in range(1, fun_test.shared_variables["volume_count"], 1):
                            fio_output[combo][mode] = {}
                            fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                                                 rw=mode,
                                                                                 bs=fio_block_size,
                                                                                 iodepth=fio_iodepth,
                                                                                 rwmixread=25,
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

                    # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                    fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                                   self.iter_interval)

        # Getting the volume stats after the FIO test
        command_result = {}
        final_volume_stats[combo][mode] = {}
        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            final_volume_stats[combo][mode][x] = {}
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                         fun_test.shared_variables["vol_data"][x]["uuid"],
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
            final_volume_stats[combo][mode][x] = command_result["data"]
            fun_test.log("Volume Status at the end of the test:")
            fun_test.log(final_volume_stats[combo][mode][x])

        command_result = {}
        final_crypto_stats[combo][mode] = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        fun_test.simple_assert(command_result["status"], "Final crypto stats of DUT Instance 0")
        final_crypto_stats[combo][mode] = command_result["data"]

        encrypt_status = self.volume_details["encrypt"]
        if encrypt_status:
            for x in range(1, fun_test.shared_variables["volume_count"], 1):
                for key, value in final_volume_stats[combo][mode][x].items():
                    if key == "num_reads":
                        total_vol_reads = value
                    elif key == "num_writes":
                        total_vol_writes = value
                volume_ops = total_vol_reads + total_vol_writes
                fun_test.shared_variables["total_volume_ops"] += volume_ops

            for key, value in final_crypto_stats[combo][mode].items():
                if key == "cryptofilter_aes_xts":
                    total_crypto_ops = value
                    print "Total Crypto ops is " + str(total_crypto_ops)

        fun_test.test_assert(expression=fun_test.shared_variables["total_volume_ops"] == total_crypto_ops,
                             message="No errors in crypto operations")

        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        for x in range(1, fun_test.shared_variables["volume_count"], 1):
            command_result = {}
            command_result = self.storage_controller.volume_detach_remote(ns_id=x,
                                                                          uuid=fun_test.shared_variables["vol_data"]
                                                                          [x]["uuid"],
                                                                          remote_ip=self.linux_host.internal_ip)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detaching Volume from DUT Instance 0")

            command_result = {}
            command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   name=fun_test.shared_variables["vol_data"]
                                                                   [x]["name"],
                                                                   uuid=fun_test.shared_variables["vol_data"]
                                                                   [x]["uuid"],
                                                                   type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting Volume")
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
    bltscript.add_test_case(VolumeKey512())
    bltscript.add_test_case(WrongKey())
    bltscript.add_test_case(WrongTweak())
    bltscript.add_test_case(MultipleBltKey256())
    bltscript.add_test_case(MultipleBltKey512())
    bltscript.add_test_case(CreateDelete256())
    bltscript.add_test_case(CreateDelete512())
    bltscript.run()
