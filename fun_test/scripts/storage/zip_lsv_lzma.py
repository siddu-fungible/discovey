from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator


'''
Script to create lsv volume with zip/encryption/CRC, run fio and check stats
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
        }
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
        }
    }
}


class LSVVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        self.storage_controller.disconnect()


class LSVVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        benchmark_parsing = True
        self.my_shared_variables = {}

        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("json file being used: {}".format(testcase_file))
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

        if ('zip_params_to_monitor' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['zip_params_to_monitor']):
            benchmark_parsing = False
            fun_test.critical("Expected zip stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        if ('params_to_monitor_per_attach' not in testcase_dict[testcase] or
                not testcase_dict[testcase]['params_to_monitor_per_attach']):
            benchmark_parsing = False
            fun_test.critical("Expected zip/crypto stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, testcase_dict))

        if self.encrypt:
            if ('enc_params_to_monitor' not in testcase_dict[testcase] or
                    not testcase_dict[testcase]['enc_params_to_monitor']):
                benchmark_parsing = False
                fun_test.critical("Expected encryption stats needed for this {} testcase is not available in "
                                  "the {} file".format(testcase, testcase_dict))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))


        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.linux_host = self.topology.get_tg_instance(tg_index=0)
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        destination_ip = self.dut.data_plane_ip

        for key in self.params_to_monitor_per_attach:
            initial_value = 0
            prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
            fun_test.log(command_result["data"])
            if command_result["data"]:
                initial_value = command_result["data"]
            self.my_shared_variables["initial_" + str(key)] = initial_value

        self.uuids = {}
        self.uuids["blt"] = []

        # Configuring the controller
        command_result = self.storage_controller.command(command="enable_counters", legacy=True, command_duration=5)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance 0")

        command_result = self.storage_controller.ip_cfg(ip=self.dut.data_plane_ip,
                                                        command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT instance 0".format(self.dut.data_plane_ip))

        # Create BLT
        this_uuid = utils.generate_uuid()
        self.uuids["blt"].append(this_uuid)
        if self.CRC_BLT:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["blt"],
                                                                capacity=self.volume_capacity["blt"],
                                                                block_size=self.volume_block["blt"],
                                                                name="blt" + str(1),
                                                                uuid=this_uuid,
                                                                crc=self.CRC_ALG_BLT,
                                                                command_duration=self.command_timeout)
        else:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["blt"],
                                                                capacity=self.volume_capacity["blt"],
                                                                block_size=self.volume_block["blt"],
                                                                name="blt" + str(1),
                                                                uuid=this_uuid,
                                                                command_duration=self.command_timeout)

        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create BLT volume ")

        # Configuring the Journal volume which is a mandatory one for the LSV
        self.uuids["jvol"] = utils.generate_uuid()
        if self.CRC_JVOL:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["jvol"],
                                                                capacity=self.volume_capacity["jvol"],
                                                                block_size=self.volume_block["jvol"],
                                                                name="jvol1", uuid=self.uuids["jvol"],
                                                                crc=self.CRC_ALG_JVOL,
                                                                command_duration=self.command_timeout)
        else:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["jvol"],
                                                                capacity=self.volume_capacity["jvol"],
                                                                block_size=self.volume_block["jvol"],
                                                                name="jvol1", uuid=self.uuids["jvol"],
                                                                command_duration=self.command_timeout)

        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create Journal volume ")

        # Configuring the LSV
        xts_key = utils.generate_key(self.key_sz)
        xts_tweak = utils.generate_key(self.tweak_sz)
        self.uuids["lsv"] = utils.generate_uuid()
        if self.CRC_LSV:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["lsv"],
                                                                capacity=self.volume_capacity["lsv"],
                                                                block_size=self.volume_block["lsv"],
                                                                name="lsv1", uuid=self.uuids["lsv"],
                                                                compress=self.compress,
                                                                zip_effort=self.zip_effort,
                                                                zip_filter=self.zfilter,
                                                                encrypt=self.encrypt,
                                                                key=xts_key,
                                                                xtweak=xts_tweak,
                                                                group=1,
                                                                jvol_uuid=self.uuids["jvol"],
                                                                pvol_id=self.uuids["blt"],
                                                                crc=self.CRC_ALG_LSV,
                                                                command_duration=self.command_timeout)
        else:
            command_result = self.storage_controller.create_volume(
                                                                type=self.volume_types["lsv"],
                                                                capacity=self.volume_capacity["lsv"],
                                                                block_size=self.volume_block["lsv"],
                                                                name="lsv1", uuid=self.uuids["lsv"],
                                                                compress=self.compress,
                                                                zip_effort=self.zip_effort,
                                                                zip_filter=self.zfilter,
                                                                encrypt=self.encrypt,
                                                                key=xts_key,
                                                                xtweak=xts_tweak,
                                                                group=1,
                                                                jvol_uuid=self.uuids["jvol"],
                                                                pvol_id=self.uuids["blt"],
                                                                command_duration=self.command_timeout)

        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create LS volume ")
        attach_uuid = self.uuids["lsv"]

        # Attaching/Exporting the LS volume to the external server
        command_result = self.storage_controller.volume_attach_remote(
                                                                    ns_id=self.ns_id,
                                                                    uuid=attach_uuid,
                                                                    remote_ip=self.linux_host.internal_ip,
                                                                    command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Attaching LS volume ")

        self.lsv_info = "LSV_X_Setup"
        fun_test.shared_variables[self.lsv_info] = {}
        fun_test.shared_variables[self.lsv_info]["uuids"] = self.uuids

    def run(self):
        testcase = self.__class__.__name__
        destination_ip = self.dut.data_plane_ip
        self.uuids = fun_test.shared_variables[self.lsv_info]["uuids"]
        test_result = True
        adjust_fio_read_counters = False

        per_volume_zip_stats = {"accumulated_out_bytes", "compress_done", "compress_fails",
                                "compress_reqs", "uncompress_done", "uncompress_fails",
                                "uncompress_reqs", "uncompressible"}

        # Take stats before running fio
        for key in self.zip_params_to_monitor:
            initial_value = 0
            if key not in per_volume_zip_stats:
                prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
            else:
                prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                       self.uuids["lsv"], "compression",
                                                       str(key))
            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
            fun_test.log(command_result["data"])
            if command_result["data"]:
                initial_value = command_result["data"]
            self.my_shared_variables["initial_" + str(key)] = initial_value

        for key in self.enc_params_to_monitor:
            initial_value = 0
            prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
            fun_test.log(command_result["data"])
            if command_result["data"]:
                initial_value = command_result["data"]
            self.my_shared_variables["initial_" + str(key)] = initial_value

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth
        fio_result = {}
        fio_output = {}
        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}

            for mode in self.fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size and IO depth set to {} & {} for the LSV "
                             " ".format(mode, fio_block_size, fio_iodepth))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode,
                                                                     bs=fio_block_size, iodepth=fio_iodepth,
                                                                     **self.fio_cmd_args)
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                command_result = self.storage_controller.peek("storage", command_duration=5)
                fun_test.log(command_result)
                if (mode == "read") or (mode == "randread"):
                    adjust_fio_read_counters = True
                if (mode == "write") or (mode == "randwrite") or (mode == "rw") or (mode == "randrw"):
                    fun_test.log("COMPRESSION STATS AFTER FIO mode:{} fio-bs:{} ".format(mode, fio_block_size))
                    for key, value in self.zip_params_to_monitor.items():
                        if key not in per_volume_zip_stats:
                            prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                        else:
                            prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                             self.uuids["lsv"], "compression",
                                                             str(key))
                        command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                        fun_test.log(command_result["data"])

                    if self.encrypt:
                        fun_test.log("ENCRYPTION STATS AFTER FIO mode:{} fio-bs:{} ".format(mode, fio_block_size))
                        for key, value in self.enc_params_to_monitor.items():
                            prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                            fun_test.log(command_result["data"])
        # take the params_to_monitor_per_attach params again and verify
        for key, value in self.params_to_monitor_per_attach.items():
            final_value = 0
            prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
            fun_test.log(command_result["data"])
            if command_result["data"]:
                final_value = command_result["data"]
            if final_value - self.my_shared_variables["initial_" + str(key)] == value:
                fun_test.add_checkpoint("attach specific stats match: " + str(key).format(self),
                                        "PASSED",
                                        value,
                                        final_value - self.my_shared_variables["initial_" + str(key)])
            else:
                fun_test.add_checkpoint("attach specific stats dont match: " + str(key).format(self),
                                        "Failed",
                                        value,
                                        final_value - self.my_shared_variables["initial_" + str(key)])
                test_result = False
        # take the final stats and verify
        for key, value in self.zip_params_to_monitor.items():
            if key not in per_volume_zip_stats:
                prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
            else:
                prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                       self.uuids["lsv"], "compression",
                                                       str(key))
            command_result = self.storage_controller.peek(prop_tree, command_duration=5)
            fun_test.log(command_result["data"])
            if key == "accumulated_out_bytes":
                if command_result["data"] and (command_result["data"] - self.expected_compressed_bytes < 200):
                    fun_test.add_checkpoint("zip RATIO: " + str(key) + " :0.005 x input: " + str(len(self.fio_bs_iodepth))
                                            + "x " +
                                            self.fio_cmd_args["size"].format(self),
                                            "PASSED",
                                            self.expected_compressed_bytes,
                                            command_result["data"])
                else:
                    fun_test.add_checkpoint("zip ratio " + str(key) + " not 0.005 x input " + str(len(self.fio_bs_iodepth)) +
                                            "x " +
                                            self.fio_cmd_args["size"].format(self),
                                            "Failed",
                                            self.expected_compressed_bytes,
                                            command_result["data"])
                    test_result = False
            elif command_result["data"] - self.my_shared_variables["initial_" + str(key)] == value:
                fun_test.add_checkpoint("zip stats match: " + str(key).format(self),
                                        "PASSED",
                                        value,
                                        command_result["data"] - self.my_shared_variables["initial_" + str(key)])
            else:
                fun_test.add_checkpoint("zip stats dont match: " + str(key).format(self),
                                        "Failed",
                                        value,
                                        command_result["data"] - self.my_shared_variables["initial_" + str(key)])
                test_result = False
            if self.encrypt:
                for key, value in self.enc_params_to_monitor.items():
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"] - self.my_shared_variables["initial_" + str(key)] == value:
                        fun_test.add_checkpoint("enc stats match: " + str(key).format(self),
                                                "PASSED",
                                                value,
                                                command_result["data"] - self.my_shared_variables["initial_" + str(key)])
                    else:
                        fun_test.add_checkpoint("enc stats dont match: " + str(key).format(self),
                                                "Failed",
                                                value,
                                                command_result["data"] - self.my_shared_variables["initial_" + str(key)])
                        test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        # detach and delete LSV
        command_result = self.storage_controller.volume_detach_remote(ns_id=self.ns_id,
                                                                      uuid=self.uuids["lsv"],
                                                                      remote_ip=self.linux_host.internal_ip)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Detaching of LSV")

        command_result = self.storage_controller.delete_volume(capacity=self.volume_capacity["lsv"],
                                                               block_size=self.volume_block["lsv"],
                                                               uuid=self.uuids["lsv"],
                                                               type=self.volume_types["lsv"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting of LSV volume")

        # delete jvol
        command_result = self.storage_controller.delete_volume(capacity=self.volume_capacity["jvol"],
                                                               block_size=self.volume_block["jvol"],
                                                               uuid=self.uuids["jvol"],
                                                               type=self.volume_types["jvol"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting of JVOL ")

        # delete blt
        command_result = self.storage_controller.delete_volume(capacity=self.volume_capacity["blt"],
                                                               block_size=self.volume_block["blt"],
                                                               uuid=self.uuids["blt"][0],
                                                               type=self.volume_types["blt"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting of BLT ")
        test_result = True
        fun_test.test_assert(test_result, self.summary)

        self.storage_controller.disconnect()


class LSVLZMAFioSeqWriteSeqRead(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="fio Sequential Write & Read on  LSV volume with compression",
                              steps="""
        1. Create 1 BLT volume on dut instance 0.
        2. Create a jvol and an LS volume on top of the BLT volume.
        3. Export (Attach) the above LS volume to external Linux instance/container. 
        4. Run the FIO sequential write and read test 
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqRead, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqRead, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqRead, self).cleanup()


class LSVLZMAFioRandWriteRandRead(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="fio Random Write & Read on LS volume with compression",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioRandWriteRandRead, self).setup()

    def run(self):
        super(LSVLZMAFioRandWriteRandRead, self).run()

    def cleanup(self):
        super(LSVLZMAFioRandWriteRandRead, self).cleanup()


class LSVLZMAFioRW(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="fio RW on LS volume with compression",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO

        """)

    def setup(self):
        super(LSVLZMAFioRW, self).setup()

    def run(self):
        super(LSVLZMAFioRW, self).run()

    def cleanup(self):
        super(LSVLZMAFioRW, self).cleanup()


class LSVLZMAFioRandRW(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="fio RandRW on LS volume with compression",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO

        """)

    def setup(self):
        super(LSVLZMAFioRandRW, self).setup()

    def run(self):
        super(LSVLZMAFioRandRW, self).run()

    def cleanup(self):
        super(LSVLZMAFioRandRW, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnBLT(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="FIO Random Write/Read compression & CRC32 on BLT",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLT, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLT, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLT, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOL(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="FIO Random Write/Read compression & CRC32 on JVOL",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOL, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOL, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOL, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnLSV(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="FIO Random Write/Read compression & CRC32 on LSV",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSV, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSV, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSV, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWthEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Sequential Write & Read only fio on  LSV volume with compression and Encryption",
                              steps="""
        1. Create 1 BLT volume on dut instance 0.
        2. Create a jvol and an LS volume on top of the BLT volume.
        4. Export (Attach) the above LS volume to external Linux instance/container. 
        5. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWthEnc, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWthEnc, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWthEnc, self).cleanup()


class LSVLZMAFioRandWriteRandReadWthEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Random Write & Read only fio on LS volume with compression and Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioRandWriteRandReadWthEnc, self).setup()

    def run(self):
        super(LSVLZMAFioRandWriteRandReadWthEnc, self).run()

    def cleanup(self):
        super(LSVLZMAFioRandWriteRandReadWthEnc, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnBLTWthEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="FIO Random Write/Read compression & CRC32 on BLT with Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLTWthEnc, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLTWthEnc, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLTWthEnc, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOLWthEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="FIO Random Write/Read compression & CRC32 on JVOL with Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOLWthEnc, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOLWthEnc, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOLWthEnc, self).cleanup()


class LSVLZMAFioSeqWriteSeqReadWithCRCOnLSVWthEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="FIO Random Write/Read compression & CRC32 on LSV with Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSVWthEnc, self).setup()

    def run(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSVWthEnc, self).run()

    def cleanup(self):
        super(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSVWthEnc, self).cleanup()


class LSVLZMAStressPlain(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=13,
                              summary="FIO compression stress",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAStressPlain, self).setup()

    def run(self):
        super(LSVLZMAStressPlain, self).run()

    def cleanup(self):
        super(LSVLZMAStressPlain, self).cleanup()


class LSVLZMAStressPlainCRC(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=14,
                              summary="FIO compression stress with CRC32",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAStressPlainCRC, self).setup()

    def run(self):
        super(LSVLZMAStressPlainCRC, self).run()

    def cleanup(self):
        super(LSVLZMAStressPlainCRC, self).cleanup()


class LSVLZMAStressEnc(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=15,
                              summary="FIO compression stress with Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAStressEnc, self).setup()

    def run(self):
        super(LSVLZMAStressEnc, self).run()

    def cleanup(self):
        super(LSVLZMAStressEnc, self).cleanup()


class LSVLZMAStressEncCRC(LSVVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=16,
                              summary="FIO tress with compression, CRC32 and Encryption",
                              steps="""
        1. Create 1 BLT volume in dut instance 0.
        2. Create a LS volume on top of the BLT volume .
        3. Export (Attach) the above LS volume based to external Linux instance/container.
        4. Run the FIO
        
        """)

    def setup(self):
        super(LSVLZMAStressEncCRC, self).setup()

    def run(self):
        super(LSVLZMAStressEncCRC, self).run()

    def cleanup(self):
        super(LSVLZMAStressEncCRC, self).cleanup()


if __name__ == "__main__":

    lsvscript = LSVVolumeLevelScript()
    '''
    # LZMA filter is not enabled in FunOS yet SWOS-3666
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqRead())
    lsvscript.add_test_case(LSVLZMAFioRandWriteRandRead())

    lsvscript.add_test_case(LSVLZMAFioRW())
    lsvscript.add_test_case(LSVLZMAFioRandRW())

    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLT())
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOL())
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSV())
    
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWthEnc())

    lsvscript.add_test_case(LSVLZMAFioRandWriteRandReadWthEnc())
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnBLTWthEnc())
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnJVOLWthEnc())
    lsvscript.add_test_case(LSVLZMAFioSeqWriteSeqReadWithCRCOnLSVWthEnc())


    #LZMA STRESS TESTS
    lsvscript.add_test_case(LSVLZMAStressPlain())
    lsvscript.add_test_case(LSVLZMAStressPlainCRC())
    lsvscript.add_test_case(LSVLZMAStressEnc())
    lsvscript.add_test_case(LSVLZMAStressEncCRC())
    '''
    lsvscript.run()
