from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.storage_controller import StorageController
from lib.host.linux import *
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.templates.security.xts_openssl_template import XtsOpenssl

topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 1,
                    "type": DutInterface.INTERFACE_TYPE_PCIE,
                    "vm_start_mode": "VM_START_MODE_QEMU_PLUS_DPCSH",
                    "vm_host_os": "fungible_ubuntu"
                }
            },
            "start_mode": "START_MODE_QEMU_PLUS_DPCSH"
        }
    }
}


class CryptoCoreTest(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Setup qemu host for EP
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        # self.topology_obj_helper.save(file_name="/tmp/pickle.pkl")
        # self.topology = self.topology_obj_helper.load(file_name="/tmp/pickle.pkl")
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance")
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["xts_ssl"] = False

    def cleanup(self):
        # pass
        if self.topology:
            self.storage_controller.disconnect()
            self.topology.cleanup()


class CryptoCore(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
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

        if self.data_size > self.blt_details["capacity"]:
            fun_test.test_assert(False, "Data size to write {} is greater than the capacity of BLT {}".
                                 format(self.data_size, self.blt_details["capacity"]))

        self.topology = fun_test.shared_variables["topology"]
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.dut = self.topology.get_dut_instance(index=0)
        self.qemu = QemuStorageTemplate(host=self.host, dut=self.dut)
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.funos_running = True
        if not fun_test.shared_variables["xts_ssl"]:
            self.xts_ssl_template = XtsOpenssl(self.host)
            install_status = self.xts_ssl_template.install_ssl()
            fun_test.test_assert(install_status, "Openssl installation")
            fun_test.shared_variables["xts_ssl"] = True
        else:
            self.xts_ssl_template = XtsOpenssl(self.host)
        # install_status = self.host.install_package("fio")
        # fun_test.test_assert(install_status, "fio installed successfully")

        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")

        if self.encrypt:
            # Getting initial crypto filter stats
            initial_filter_values = {}
            for filter_param in self.filter_params:
                crypto_props_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", filter_param)

                command_result = self.storage_controller.peek(crypto_props_tree)
                if command_result["data"] is None:
                    command_result["data"] = 0
                initial_filter_values[filter_param] = command_result["data"]

        self.uuid = {}
        self.blt_uuid = utils.generate_uuid()
        self.jvol_uuid = utils.generate_uuid()
        self.lsv_uuid = utils.generate_uuid()
        self.xts_key = utils.generate_key(self.key_size)
        self.xts_tweak = utils.generate_key(self.xtweak_size)

        self.blt_capacity = (self.blt_details["capacity"] * self.lsv_head / 100) + self.blt_details["capacity"]
        # Make sure the capacity is multiple of block size
        self.blt_capacity = ((self.blt_capacity + self.blt_details["block_size"] - 1) /
                             self.blt_details["block_size"]) * self.blt_details["block_size"]

        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_details["block_size"],
                                                               name="thin_block1",
                                                               uuid=self.blt_uuid,
                                                               command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Creation of BLT with uuid {}".format(self.blt_uuid))

        # Create JVol
        self.jvol_capacity = \
            self.blt_details["block_size"] * self.jvol_details["multiplier"] * self.lsv_details["chunk_size"]

        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_NV_MEMORY",
                                                               capacity=self.jvol_capacity,
                                                               block_size=self.jvol_details["block_size"],
                                                               name="jvol1",
                                                               uuid=self.jvol_uuid,
                                                               command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Creation of Jvol with uuid {}".format(self.jvol_uuid))

        # Create LSV
        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LSV",
                                                               capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="lsv1",
                                                               uuid=self.lsv_uuid,
                                                               jvol_uuid=self.jvol_uuid,
                                                               pvol_id=[self.blt_uuid],
                                                               group=1,
                                                               encrypt=self.encrypt,
                                                               key=self.xts_key,
                                                               xtweak=self.xts_tweak,
                                                               command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Creation of LSV with uuid {}".format(self.lsv_uuid))

        # Attach the volume over PCIe
        command_result = self.storage_controller.volume_attach_pcie(ns_id=1,
                                                                    uuid=self.lsv_uuid,
                                                                    command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Attaching LSV with uuid {}".format(self.lsv_uuid))

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
                multiplier = 1
                # Computing expected filter value
                if filter_param != "vol_decrypt_filter_added" and filter_param != "vol_encrypt_filter_added":
                    evalue = 2 * multiplier
                else:
                    evalue = 1 * multiplier
                diff_filter_values[filter_param] = \
                    final_filter_values[filter_param] - initial_filter_values[filter_param]
                fun_test.test_assert(expression=diff_filter_values[filter_param] == evalue,
                                     message="Crypto filter {} count {} matches expected count {}".
                                     format(filter_param, diff_filter_values[filter_param], evalue))

    def run(self):
        testcase = self.__class__.__name__

        test_run_status = True

        # Stop services on host
        self.qemu.stop_host_services()

        # Remove *.txt files from /tmp
        self.host.remove_file("/tmp/*.txt")

        # Create a file on host used as input for nvme write
        self.host.command("while true ; do printf DEADBEEF; done | head -c {} > /tmp/input_file.txt".
                          format(self.write_size))
        self.md5sum_input = self.qemu.md5sum(file_name="/tmp/input_file.txt")
        fun_test.simple_assert(self.md5sum_input, "Computing md5sum for input file")
        fun_test.log("The md5sum of the input file is {}".format(self.md5sum_input))

        # Check if device is present or else reload nvme driver
        lsblk_output = self.host.command("lsblk -o NAME | grep -i nvme0")
        if "nvme0" in lsblk_output:
            fun_test.log("Disk is seen in lsblk {}".format(lsblk_output))
        else:
            nvme_reload = self.host.nvme_restart()
            fun_test.test_assert(nvme_reload, "nvme driver module reloaded")
            fun_test.sleep("Waiting for NVMe reload to complete", seconds=5)
            nvme_controller = self.host.command("ls /dev/nvme*")
            if "cannot" in nvme_controller:
                fun_test.test_assert(False, "NVMe controller not found")
            lsblk_output = self.host.command("lsblk -o NAME | grep -i nvme0")
            if "nvme0" not in lsblk_output:
                fun_test.test_assert(False, "NVME device not found.")

        self.nvme_block_device = self.nvme_device + "n1"

        lsv_write = {}
        lsv_read = {}
        lsv_read_cipher = {}
        lsv_read_plain = {}
        self.md5sum_cipher = []
        self.total_num_blocks = self.data_size / self.write_size
        write_block_count = self.write_size / self.blt_details["block_size"]

        # Do a NVMe write/read based on total num of blocks
        start_count = 0
        for i in range(0, self.total_num_blocks, 1):
            blk_count = write_block_count - 1
            lsv_write[i] = {}
            lsv_read[i] = {}
            lsv_read_cipher[i] = {}
            lsv_read_plain[i] = {}

            lsv_write[i] = self.qemu.nvme_write(device=self.nvme_block_device,
                                                start=start_count,
                                                count=blk_count,
                                                size=self.write_size,
                                                data="/tmp/input_file.txt")
            fun_test.simple_assert(expression=lsv_write[i] == "Success",
                                   message="Write failed with {} on LSV".format(lsv_write[i]))

            lsv_read[i] = self.qemu.nvme_read(device=self.nvme_block_device,
                                              start=start_count,
                                              count=blk_count,
                                              size=self.write_size,
                                              data="/tmp/read_lsv" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=lsv_write[i] == "Success",
                                   message="Read failed with {} on LSV, LBA {}".format(lsv_read[i], start_count))

            self.md5sum_output = self.qemu.md5sum(file_name="/tmp/read_lsv" + "_lba_" + str(start_count))
            fun_test.simple_assert(self.md5sum_output, "Computing md5sum for output file")
            fun_test.simple_assert(expression=self.md5sum_input == self.md5sum_output,
                                   message="The md5sum doesn't match for LBA {}, input {}, output {}".
                                   format(start_count, self.md5sum_input, self.md5sum_output))

            # Now umount volume and mount without encryption
            command_result = self.storage_controller.volume_detach_pcie(ns_id=1,
                                                                        uuid=self.lsv_uuid,
                                                                        command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Detach LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.unmount_volume(type="VOL_TYPE_BLK_LSV",
                                                                    uuid=self.lsv_uuid,
                                                                    name="lsv1")
            fun_test.simple_assert(command_result["status"], "Unmount LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LSV",
                                                                  capacity=self.blt_details["capacity"],
                                                                  block_size=self.blt_details["block_size"],
                                                                  uuid=self.lsv_uuid,
                                                                  jvol_uuid=self.jvol_uuid,
                                                                  pvol_id=[self.blt_uuid],
                                                                  group=1,
                                                                  command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Mount LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.volume_attach_pcie(ns_id=1,
                                                                        uuid=self.lsv_uuid,
                                                                        command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching LSV with uuid {}".format(self.lsv_uuid))

            lsv_read_cipher[i] = self.qemu.nvme_read(device=self.nvme_block_device,
                                                     start=start_count,
                                                     count=blk_count,
                                                     size=self.write_size,
                                                     data="/tmp/enc_read_lsv" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=lsv_read_cipher[i] == "Success",
                                   message="Cipher Read failed with {} on LSV, LBA {}".
                                   format(lsv_read_cipher[i], start_count))

            cipher_md5sum = self.qemu.md5sum(file_name="/tmp/enc_read_lsv" + "_lba_" + str(start_count))
            self.md5sum_cipher.append(cipher_md5sum)

            # Mount LSV with encryption now
            command_result = self.storage_controller.volume_detach_pcie(ns_id=1,
                                                                        uuid=self.lsv_uuid,
                                                                        command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Detach LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.unmount_volume(type="VOL_TYPE_BLK_LSV",
                                                                    uuid=self.lsv_uuid,
                                                                    name="lsv1")
            fun_test.simple_assert(command_result["status"], "Unmount LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LSV",
                                                                  capacity=self.blt_details["capacity"],
                                                                  block_size=self.blt_details["block_size"],
                                                                  uuid=self.lsv_uuid,
                                                                  jvol_uuid=self.jvol_uuid,
                                                                  pvol_id=[self.blt_uuid],
                                                                  group=1,
                                                                  encrypt=self.encrypt,
                                                                  key=self.xts_key,
                                                                  xtweak=self.xts_tweak,
                                                                  command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Mount LSV with uuid {}".format(self.lsv_uuid))

            command_result = self.storage_controller.volume_attach_pcie(ns_id=1,
                                                                        uuid=self.lsv_uuid,
                                                                        command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching LSV with uuid {}".format(self.lsv_uuid))

            lsv_read_plain[i] = self.qemu.nvme_read(device=self.nvme_block_device,
                                                    start=start_count,
                                                    count=blk_count,
                                                    size=self.write_size,
                                                    data="/tmp/plain_read_lsv" + "_lba_" + str(start_count))
            fun_test.test_assert(expression=lsv_read_plain[i] == "Success",
                                 message="Plain txt read completed with {} on LSV, LBA {}".
                                 format(lsv_read_plain[i], start_count))

            self.md5sum_plain_read = self.qemu.md5sum(file_name="/tmp/plain_read_lsv" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=self.md5sum_input == self.md5sum_plain_read,
                                   message="There is a mismatch in data read after mount with encryption, input "
                                           "md5sum {}, read md5sum {} for LBA {}".
                                   format(self.md5sum_input, self.md5sum_plain_read, start_count))

            # Verify the output with openssl if write_size is 4k
            if self.write_size == 4096:
                hex_lba = hex(start_count)
                # Remove 0x
                hex_lba = hex_lba[2:]
                # LBA is denoted as 0x01 0x02
                if len(hex_lba) == 1:
                    hex_lba = str(0) + hex_lba
                lba_tweak = hex_lba.ljust(16, '0')
                tweak = lba_tweak + self.xts_tweak
                # Encrypt using openssl
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=self.xts_key,
                    iv=tweak,
                    input_file="/tmp/input_file.txt",
                    output_file="/tmp/ssl_encrypted" + "_lba_" + str(start_count),
                    encrypt=True)
                fun_test.simple_assert(ssl_result, "Encrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    self.xts_key,
                                                                    tweak,
                                                                    "/tmp/ssl_encrypted" + "_lba_" + str(start_count)))

                # Decrypt encrypted LBA data
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=self.xts_key, iv=tweak,
                    input_file="/tmp/enc_read_lsv" + "_lba_" + str(start_count),
                    output_file="/tmp/ssl_decrypted" + "_lba_" + str(start_count),
                    encrypt=False)
                fun_test.simple_assert(ssl_result, "Decrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    self.xts_key,
                                                                    tweak,
                                                                    "/tmp/enc_read_lsv" + "_lba_" + str(start_count)))
                ssl_encrypted_md5sum = self.qemu.md5sum(file_name="/tmp/ssl_encrypted" + "_lba_" + str(start_count))
                ssl_decrypted_md5sum = self.qemu.md5sum(file_name="/tmp/ssl_decrypted" + "_lba_" + str(start_count))
                fun_test.test_assert(expression=ssl_encrypted_md5sum == self.md5sum_cipher[i],
                                     message="Compare md5sum of Encrypted file from openssl for LBA {}".
                                     format(start_count))
                fun_test.test_assert(expression=self.md5sum_input == ssl_decrypted_md5sum,
                                     message="Compare md5sum of Decrypted file from openssl for LBA {}".
                                     format(start_count))

            start_count += write_block_count
        fun_test.simple_assert(expression=len(self.md5sum_cipher) == len(set(self.md5sum_cipher)),
                               message="There seems to be same encrypted data on different LBA, {}".
                               format(self.md5sum_cipher))

    def cleanup(self):
        if hasattr(self, "host_disconnect") and self.host_disconnect:
            self.host.disconnect()

        command_result = self.storage_controller.volume_detach_pcie(ns_id=1,
                                                                    uuid=self.lsv_uuid,
                                                                    command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Detach LSV with uuid {}".format(self.lsv_uuid))

        command_result = self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="lsv1",
                                                               uuid=self.lsv_uuid,
                                                               type="VOL_TYPE_BLK_LSV")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleted LSV with uuid {}".format(self.lsv_uuid))
        command_result = self.storage_controller.delete_volume(capacity=self.jvol_capacity,
                                                               block_size=self.jvol_details["block_size"],
                                                               name="jvol1",
                                                               uuid=self.jvol_uuid,
                                                               type="VOL_TYPE_BLK_NV_MEMORY")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleted Journal with uuid {}".format(self.jvol_uuid))
        command_result = self.storage_controller.delete_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               uuid=self.blt_uuid,
                                                               block_size=self.blt_details["block_size"],
                                                               name="thin_block1",
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Delete BLT with uuid {}".format(self.blt_uuid))

        # TODO SWOS-3597
        fun_test.log("Volume stats after cleanup")
        self.storage_props_tree = "{}/{}".format("storage", "volumes")
        command_result = self.storage_controller.peek(self.storage_props_tree)


class Key256Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Write & Read on 256bit encrypted LSV using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a LSV with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Write & Read on 512bit encrypted LSV using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a LSV with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key256Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Write & Read on 256bit encrypted LSV using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a LSV with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Write & Read on 512bit encrypted LSV using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a LSV with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


if __name__ == "__main__":
    crypto_script = CryptoCoreTest()
    crypto_script.add_test_case(Key256Write4k())
    crypto_script.add_test_case(Key512Write4k())
    crypto_script.add_test_case(Key256Write8k())
    crypto_script.add_test_case(Key512Write8k())

    crypto_script.run()
