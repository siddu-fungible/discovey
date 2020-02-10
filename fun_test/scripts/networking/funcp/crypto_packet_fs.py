from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.host.linux import *
from lib.templates.security.xts_openssl_template import XtsOpenssl
from asset.asset_manager import *
import re
import ipaddress


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        fun_test.shared_variables["xts_ssl"] = False

    def cleanup(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        for host in host_dict["f1_0"]:
            host.disconnect()
        for host in host_dict["f1_1"]:
            host.disconnect()


class BringupSetup(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "f10_retimer" in job_inputs:
            f10_retimer = str(job_inputs["f10_retimer"]).strip("[]").replace(" ", "")
        else:
            f10_retimer = 0
        if "f11_retimer" in job_inputs:
            f11_retimer = str(job_inputs["f11_retimer"]).strip("[]").replace(" ", "")
        else:
            f11_retimer = 0
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --serial --all_100g --dpc-uart " \
                         "retimer={} --mgmt".format(f10_retimer)
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --serial --all_100g --dpc-uart " \
                         "retimer={} --mgmt".format(f11_retimer)
        if "deadbeef" in job_inputs:
            fun_test.shared_variables["data_pattern"] = job_inputs["deadbeef"]
        else:
            fun_test.shared_variables["data_pattern"] = False

        topology_helper = TopologyHelper()
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup

        if deploy_setup:
            funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
            funcp_obj.cleanup_funcp()
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            servers_list = []

            for server in servers_mode:
                critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
                servers_list.append(server)

            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}}
                                               )
            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")
            fs = topology.get_dut_instance(index=0)
            f10_instance = fs.get_f1(index=0)
            f11_instance = fs.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()
            come_obj = fs.get_come()
            fun_test.shared_variables["come_obj"] = come_obj
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("iptables -F")
            come_obj.sudo_command("ip6tables -F")
            come_obj.sudo_command("dmesg -c > /dev/null")

            fun_test.log("Getting host details")
            host_dict = {"f1_0": [], "f1_1": []}
            for i in range(0, 23):
                if i <= 11:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_0"]:
                            host_dict["f1_0"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
                elif i > 11 <= 23:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_1"]:
                            host_dict["f1_1"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
            fun_test.shared_variables["hosts_obj"] = host_dict

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])
        else:
            am = AssetManager()
            th = TopologyHelper(spec=am.get_test_bed_spec(name=fs_name))
            topology = th.get_expanded_topology()
            dut = topology.get_dut(index=0)
            dut_name = dut.get_name()
            fs_spec = fun_test.get_asset_manager().get_fs_spec(name=dut_name)
            fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True)
            come_obj = fs_obj.get_come()
            f10_instance = fs_obj.get_f1(index=0)
            f11_instance = fs_obj.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()
            fun_test.shared_variables["come_obj"] = come_obj

            fun_test.log("Getting host info")
            host_dict = {"f1_0": [], "f1_1": []}
            temp_host_list = []
            temp_host_list1 = []
            expanded_topology = topology_helper.get_expanded_topology()
            pcie_hosts = expanded_topology.get_pcie_hosts_on_interfaces(dut_index=0)
            for pcie_interface_index, host_info in pcie_hosts.iteritems():
                host_instance = fun_test.get_asset_manager().get_linux_host(host_info["name"])
                if pcie_interface_index <= 11:
                    if host_info["name"] not in temp_host_list:
                        host_dict["f1_0"].append(host_instance)
                        temp_host_list.append(host_info["name"])
                elif pcie_interface_index > 11 <= 23:
                    if host_info["name"] not in temp_host_list1:
                        host_dict["f1_1"].append(host_instance)
                        temp_host_list1.append(host_info["name"])
            fun_test.shared_variables["hosts_obj"] = host_dict

        fun_test.shared_variables["host_len_f10"] = len(host_dict["f1_0"])
        fun_test.shared_variables["host_len_f11"] = len(host_dict["f1_1"])

        fun_test.log("SETUP Done")

    def cleanup(self):
        pass


class CryptoCore(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        self.host_obj = host_dict["f1_1"][0]
        write_size = 4096
        data_size = 8192
        self.blt_block_size = 4096
        self.blt_uuid = utils.generate_uuid()
        self.command_timeout = 5
        self.storage_controller = fun_test.shared_variables["f11_storage_controller"]

        # Remove *.txt files from /tmp
        self.host_obj.sudo_command("rm -rf /tmp/*")

        if not fun_test.shared_variables["xts_ssl"]:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)
            install_status = self.xts_ssl_template.install_ssl()
            fun_test.test_assert(install_status, "Openssl installation")
            fun_test.shared_variables["xts_ssl"] = True
        else:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)

        # Create a BLT with encryption using 256 bit key
        xts_key = utils.generate_key(length=32)
        xts_tweak = utils.generate_key(length=8)
        self.blt_capacity = 67108864
        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_block_size,
                                                               name="thin_block1",
                                                               encrypt=True,
                                                               key=xts_key,
                                                               xtweak=xts_tweak,
                                                               uuid=self.blt_uuid,
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "BLT creation with encryption with uuid {}".
                             format(self.blt_uuid))

        # Create a PCIe controller
        self.controller_uuid = utils.generate_uuid()
        command_result = self.storage_controller.create_controller(ctrlr_uuid=self.controller_uuid,
                                                                   transport="PCI",
                                                                   fnid=2,
                                                                   ctlid=0,
                                                                   huid=1,
                                                                   command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"],
                             "Creation of PCIe controller with uuid {}".format(self.controller_uuid))

        # # Attach PCI controller to Vol
        command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=self.blt_uuid,
                                                                             ctrlr_uuid=self.controller_uuid,
                                                                             ns_id=1,
                                                                             command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Attaching vol to PCIe controller")

        # Create qemu object
        self.qemu = QemuStorageTemplate(host=self.host_obj, dut=0)

        # Stop services on host
        self.qemu.stop_host_services()

        # Create a file on host used as input for nvme write
        if fun_test.shared_variables["data_pattern"]:
            fun_test.log("Create a input with pattern DEADBEEF")
            self.host_obj.command("while true ; do printf DEADBEEF; done | head -c {} > /tmp/input_file.txt".
                                  format(write_size))
        else:
            fun_test.log("Create a input with random chars from urandom file")
            self.host_obj.command("tr -dc A-Za-z0-9 < /dev/urandom | head -c {} > /tmp/input_file.txt".
                                  format(write_size))
        self.md5sum_input = self.qemu.md5sum(file_name="/tmp/input_file.txt")
        fun_test.simple_assert(self.md5sum_input, "Computing md5sum for input file")
        fun_test.log("The md5sum of the input file is {}".format(self.md5sum_input))

        fun_test.log_section("nvme name")
        lsblk_out = json.loads(self.host_obj.command("lsblk -o NAME -nl -J"))
        devices_list = lsblk_out["blockdevices"]
        for element in devices_list:
            if "nvme" in element["name"]:
                nvme_block_device = "/dev/" + str(element["name"])

        blt_write = {}
        blt_read = {}
        blt_read_cipher = {}
        blt_read_plain = {}
        md5sum_cipher = []
        total_num_blocks = data_size / write_size
        write_block_count = write_size / self.blt_block_size

        # Do a NVMe write/read based on total num of blocks
        start_count = 0
        for i in range(0, total_num_blocks, 1):
            blk_count = write_block_count - 1
            blt_write[i] = {}
            blt_read[i] = {}
            blt_read_cipher[i] = {}
            blt_read_plain[i] = {}

            blt_write[i] = self.qemu.nvme_write(device=nvme_block_device,
                                                start=start_count,
                                                count=blk_count,
                                                size=write_size,
                                                data="/tmp/input_file.txt")
            fun_test.test_assert(expression=blt_write[i] == "Success",
                                 message="Write status : {}, on BLT".format(blt_write[i]))

            blt_read[i] = self.qemu.nvme_read(device=nvme_block_device,
                                              start=start_count,
                                              count=blk_count,
                                              size=write_size,
                                              data="/tmp/read_blt" + "_lba_" + str(start_count))
            fun_test.test_assert(expression=blt_write[i] == "Success",
                                 message="Read status : {}, on BLT, LBA {}".format(blt_read[i], start_count))

            self.md5sum_output = self.qemu.md5sum(file_name="/tmp/read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(self.md5sum_output, "Computing md5sum for output file")
            fun_test.simple_assert(expression=self.md5sum_input == self.md5sum_output,
                                   message="The md5sum doesn't match for LBA {}, input {}, output {}".
                                   format(start_count, self.md5sum_input, self.md5sum_output))

            # Now umount volume and mount without encryption
            command_result = self.storage_controller.detach_volume_from_controller(ns_id=1,
                                                                                   ctrlr_uuid=self.controller_uuid,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach BLT with uuid {}".format(self.blt_uuid))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                  capacity=self.blt_capacity,
                                                                  block_size=self.blt_block_size,
                                                                  name="thin_block1",
                                                                  uuid=self.blt_uuid,
                                                                  command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Mount BLT without encryption")

            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.controller_uuid,
                                                                                 ns_id=1,
                                                                                 vol_uuid=self.blt_uuid,
                                                                                 command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Attaching BLT without encryption")

            blt_read_cipher[i] = self.qemu.nvme_read(device=nvme_block_device,
                                                     start=start_count,
                                                     count=blk_count,
                                                     size=write_size,
                                                     data="/tmp/enc_read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=blt_read_cipher[i] == "Success",
                                   message="Cipher Read failed with {} on BLT, LBA {}".
                                   format(blt_read_cipher[i], start_count))

            cipher_md5sum = self.qemu.md5sum(file_name="/tmp/enc_read_blt" + "_lba_" + str(start_count))
            md5sum_cipher.append(cipher_md5sum)

            # Mount BLT with encryption now
            # TODO during unmount give type "VOL_TYPE_BLK_LSV" as it leads to a crash.
            command_result = self.storage_controller.detach_volume_from_controller(ns_id=1,
                                                                                   ctrlr_uuid=self.controller_uuid,
                                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detach BLT with uuid {}".format(self.blt_uuid))

            # command_result = self.storage_controller.unmount_volume(type="VOL_TYPE_BLK_LSV",
            #                                                         uuid=self.blt_uuid,
            #                                                         name="thin_block1")
            # fun_test.simple_assert(command_result["status"], "Unmount LSV with uuid {}".format(self.blt_uuid))

            command_result = self.storage_controller.mount_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                  capacity=self.blt_capacity,
                                                                  block_size=self.blt_block_size,
                                                                  name="thin_block1",
                                                                  encrypt=True,
                                                                  key=xts_key,
                                                                  xtweak=xts_tweak,
                                                                  uuid=self.blt_uuid,
                                                                  command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Mount BLT with encryption")

            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.controller_uuid,
                                                                                 ns_id=1,
                                                                                 vol_uuid=self.blt_uuid,
                                                                                 command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Attaching BLT with encryption")

            blt_read_plain[i] = self.qemu.nvme_read(device=nvme_block_device,
                                                    start=start_count,
                                                    count=blk_count,
                                                    size=write_size,
                                                    data="/tmp/plain_read_blt" + "_lba_" + str(start_count))
            fun_test.test_assert(expression=blt_read_plain[i] == "Success",
                                 message="Plain txt read completed with {} on BLT, LBA {}".
                                 format(blt_read_plain[i], start_count))

            md5sum_plain_read = self.qemu.md5sum(file_name="/tmp/plain_read_blt" + "_lba_" + str(start_count))
            fun_test.simple_assert(expression=self.md5sum_input == md5sum_plain_read,
                                   message="There is a mismatch in data read after mount with encryption, input "
                                           "md5sum {}, read md5sum {} for LBA {}".
                                   format(self.md5sum_input, md5sum_plain_read, start_count))

            # Verify the output with openssl if write_size is 4k
            if write_size == 4096:
                hex_lba = hex(start_count)
                # Remove 0x
                hex_lba = hex_lba[2:]
                # LBA is denoted as 0x01 0x02
                # if len(hex_lba) == 1:
                #     hex_lba = str(0) + hex_lba
                # lba_tweak = hex_lba.ljust(16, '0') #looks like this has changed now so line 351 to 353 is not needed.
                # Its 000000000000000a not 0a00000000000000
                lba_tweak = hex_lba.rjust(16, '0')
                tweak = lba_tweak + xts_tweak
                # Encrypt using openssl
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=xts_key,
                    iv=tweak,
                    input_file="/tmp/input_file.txt",
                    output_file="/tmp/ssl_encrypted" + "_lba_" + str(start_count),
                    encrypt=True)
                fun_test.simple_assert(ssl_result, "Encrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    xts_key,
                                                                    tweak,
                                                                    "/tmp/ssl_encrypted" + "_lba_" + str(start_count)))

                # Decrypt encrypted LBA data
                ssl_result = self.xts_ssl_template.compute_cipher(
                    key=xts_key, iv=tweak,
                    input_file="/tmp/enc_read_blt" + "_lba_" + str(start_count),
                    output_file="/tmp/ssl_decrypted" + "_lba_" + str(start_count),
                    encrypt=False)
                fun_test.simple_assert(ssl_result, "Decrypt using openssl for LBA {} with key {}, iv {} and input "
                                                   "file {}".format(start_count,
                                                                    xts_key,
                                                                    tweak,
                                                                    "/tmp/enc_read_blt" + "_lba_" + str(start_count)))
                ssl_encrypted_md5sum = self.qemu.md5sum(file_name="/tmp/ssl_encrypted" + "_lba_" + str(start_count))
                ssl_decrypted_md5sum = self.qemu.md5sum(file_name="/tmp/ssl_decrypted" + "_lba_" + str(start_count))
                fun_test.test_assert(expression=ssl_encrypted_md5sum == md5sum_cipher[i],
                                     message="Compare md5sum of Encrypted file from openssl for LBA {}".
                                     format(start_count))
                fun_test.test_assert(expression=self.md5sum_input == ssl_decrypted_md5sum,
                                     message="Compare md5sum of Decrypted file from openssl for LBA {}".
                                     format(start_count))

            start_count += write_block_count
        fun_test.simple_assert(expression=len(md5sum_cipher) == len(set(md5sum_cipher)),
                               message="There seems to be same encrypted data on different LBA, {}".
                               format(md5sum_cipher))

    def cleanup(self):        
        self.host_obj.disconnect()

        command_result = self.storage_controller.detach_volume_from_controller(ns_id=1,
                                                                               ctrlr_uuid=self.controller_uuid,
                                                                               command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Detach BLT with uuid {}".format(self.blt_uuid))
        
        command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.controller_uuid,
                                                                   command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Delete of controller")

        command_result = self.storage_controller.delete_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               uuid=self.blt_uuid,
                                                               block_size=self.blt_block_size,
                                                               name="thin_block1",
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Delete BLT with uuid {}".format(self.blt_uuid))

        # TODO SWOS-3597
        fun_test.log("Volume stats after cleanup")
        self.storage_props_tree = "{}/{}".format("storage", "volumes")
        command_result = self.storage_controller.peek(self.storage_props_tree)


class Key256Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Write & Read on 256bit encrypted BLT using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Write & Read on 512bit encrypted BLT using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key256Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Write & Read on 256bit encrypted BLT using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Write & Read on 512bit encrypted BLT using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


if __name__ == "__main__":
    crypto_script = ScriptSetup()
    crypto_script.add_test_case(BringupSetup())
    crypto_script.add_test_case(Key256Write4k())
    # crypto_script.add_test_case(Key512Write4k())
    # crypto_script.add_test_case(Key256Write8k())
    # crypto_script.add_test_case(Key512Write8k())

    crypto_script.run()
