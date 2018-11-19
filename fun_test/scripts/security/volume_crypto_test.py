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
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology
        # We have declared this here since when we remove volume, the counters are from zero but crypto
        # counters are not from zero.
        fun_test.shared_variables["total_volume_ops"] = 0

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


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
        destination_ip = self.dut_instance.data_plane_ip

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
            self.thin_uuid = generate_uuid()
            self.xts_key = generate_key(self.key_size)
            self.xts_tweak = generate_key(self.xtweak_size)

            command_result = self.storage_controller.create_volume(type=self.volume_details["type"],
                                                                   capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   name=self.volume_details["name"],
                                                                   uuid=self.thin_uuid,
                                                                   encrypt=self.volume_details["encrypt"],
                                                                   key=self.xts_key,
                                                                   xtweak=self.xts_tweak,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

            command_result = {}
            command_result = self.storage_controller.volume_attach_remote(ns_id=self.volume_details["ns_id"],
                                                                          uuid=self.thin_uuid,
                                                                          remote_ip=self.linux_host.internal_ip,
                                                                          command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")

            fun_test.shared_variables["blt"]["setup_created"] = True
            # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
            # Executing the FIO command to warm up the system
            # FIO use verify option : md5, sha1, sha256, sha384 etc. Check man page.
            if self.warm_up_traffic:
                fun_test.log("Executing the FIO command to warm up the system")
                fio_output = self.linux_host.remote_fio(destination_ip=destination_ip,
                                                        **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output)
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        total_vol_reads = 0
        total_vol_writes = 0

        # self.storage_controller = fun_test.shared_variables["blt"]["storage_controller"]
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"],
                                                     self.thin_uuid, "stats")
        # crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", "cryptofilter_aes_xts")
        crypto_props_tree = "{}/{}/{}".format("stats", "wus", "counts")

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_stats = {}
        final_volume_stats = {}
        diff_volume_stats = {}
        initial_stats = {}
        final_stats = {}
        diff_stats = {}
        initial_crypto_stats = {}
        final_crypto_stats = {}

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            initial_volume_stats[combo] = {}
            final_volume_stats[combo] = {}
            diff_volume_stats[combo] = {}
            initial_stats[combo] = {}
            final_stats[combo] = {}
            diff_stats[combo] = {}
            initial_crypto_stats[combo] = {}
            final_crypto_stats[combo] = {}

            for mode in self.fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = fio_iodepth
                row_data_dict["size"] = self.fio_cmd_args["size"]

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats in dictionary format
                # command_result = {}
                # initial_volume_stats[combo][mode] = {}
                # command_result = self.storage_controller.peek(storage_props_tree)
                # fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
                # initial_volume_stats[combo][mode] = command_result["data"]
                # fun_test.log("Volume Status at the beginning of the test:")
                # fun_test.log(initial_volume_stats[combo][mode])

                # command_result = {}
                # initial_crypto_stats[combo][mode] = {}
                # command_result = self.storage_controller.peek(crypto_props_tree)
                # fun_test.simple_assert(command_result["status"], "Initial crypto stats of DUT Instance 0")
                # initial_crypto_stats[combo][mode] = command_result["data"]
                # fun_test.log("Crypto Status at the beginning of the test:")
                # fun_test.log(initial_crypto_stats[combo][mode])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                if mode == "rw" or mode == "randrw":
                    fio_output[combo][mode] = {}
                    fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode,
                                                                         bs=fio_block_size, iodepth=fio_iodepth,
                                                                         rwmixread=25,
                                                                         **self.fio_cmd_args)
                else:
                    fio_output[combo][mode] = {}
                    fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode,
                                                                         bs=fio_block_size, iodepth=fio_iodepth,
                                                                         **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

        # Getting the volume stats after the FIO test
        command_result = {}
        final_volume_stats[combo][mode] = {}
        command_result = self.storage_controller.peek(storage_props_tree)
        fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
        final_volume_stats[combo][mode] = command_result["data"]
        fun_test.log("Volume Status at the end of the test:")
        fun_test.log(final_volume_stats[combo][mode])

        command_result = {}
        final_crypto_stats[combo][mode] = {}
        command_result = self.storage_controller.peek(crypto_props_tree)
        fun_test.simple_assert(command_result["status"], "Final crypto stats of DUT Instance 0")
        final_crypto_stats[combo][mode] = command_result["data"]

        encrypt_status = self.volume_details["encrypt"]
        if encrypt_status:
            for key, value in final_volume_stats[combo][mode].items():
                if key == "num_reads":
                    total_vol_reads = value
                elif key == "num_writes":
                    total_vol_writes = value
            volume_ops = total_vol_reads + total_vol_writes
            print "The Write/Read Volume ops is " + str(volume_ops)

            for key, value in final_crypto_stats[combo][mode].items():
                if key == "cryptofilter_aes_xts":
                    total_crypto_ops = value
                    print "Total Crypto ops is " + str(total_crypto_ops)

        fun_test.shared_variables["total_volume_ops"] += volume_ops
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
        command_result = {}
        command_result = self.storage_controller.volume_detach_remote(ns_id=self.volume_details["ns_id"],
                                                                      uuid=self.thin_uuid,
                                                                      remote_ip=self.linux_host.internal_ip)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Detaching Volume from DUT Instance 0")
        fun_test.sleep(message="Sleeping for {} before deleting volume", seconds=2)

        command_result = {}
        command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                               block_size=self.volume_details["block_size"],
                                                               name=self.volume_details["name"],
                                                               uuid=self.thin_uuid,
                                                               type=self.volume_details["type"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting Volume")
        self.storage_controller.disconnect()
        fun_test.shared_variables["blt"]["setup_created"] = False
        # pass


class BLTFioTestKey256(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Fio test for a volume with 256 bit key doing write,read,rw(25% read),"
                                      "random write/read, random rw(25% read) over RDS.",
                              steps='''
        1. Create a local thin block volume with encryption using 256 bit key in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO with verify for various block size and IO depth from the 
        external Linux server. 
        ''')

    def setup(self):
        super(BLTFioTestKey256, self).setup()

    def run(self):
        super(BLTFioTestKey256, self).run()

    def cleanup(self):
        super(BLTFioTestKey256, self).cleanup()


class BLTFioTestKey512(BLTCryptoVolumeTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Fio test for a volume with 512 bit key doing write,read,rw(25% read),"
                                      "random write/read, random rw(25% read) over RDS.",
                              steps='''
        1. Create a local thin block volume with encryption using 512 bit key in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO with verify for various block size and IO depth from the 
        external Linux server. 
        ''')

    def setup(self):
        super(BLTFioTestKey512, self).setup()

    def run(self):
        super(BLTFioTestKey512, self).run()

    def cleanup(self):
        super(BLTFioTestKey512, self).cleanup()


if __name__ == "__main__":
    bltscript = BLTCryptoVolumeScript()
    bltscript.add_test_case(BLTFioTestKey256())
    bltscript.add_test_case(BLTFioTestKey512())
    bltscript.run()
