"""
Author: Rushikesh Pendse
Created On: 14/08/2018

To test LSO (Large Send Offload) Feature. This test case copies various sizes files from cadence-pc-3 to cadence-pc-4
with diff mss values set on the system.
This script runs in system testing.
"""
from lib.system.fun_test import *
from lib.host.linux import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *


file_sizes_in_kbs = [10, 256, 500]
file_sizes_in_mbs = [1, 10]
file_sizes_in_gbs = [1, 2]
file_dir = "/root/files/"
mss_values = [100, 300, 1300]
source_machine = "cadence-pc-3"
target_machine = "cadence-pc-4"
target_machine_ip = "75.0.0.4"
username = "root"
password = "fun123"
md5sums = {"kbs": {10: "1276481102f218c981e0324180bafd9f",
                   256: "ec87a838931d4d5d2e94a04644788a55",
                   500: "816df6f64deba63b029ca19d880ee10a"},
           "mbs": {1: "44fdea57c9ffdee7f57cdc54fa998ebb",
                   10: "f1c9645dbc14efddc7d8a322685f26eb",
                   100: "2f282b84e7e608d5852449ed940bfc51",
                   500: "d8b61b2c0025919d5321461045c8226f",
                   900: "302a54c478b9ea36d04bf4d6e7fcca81"},
           "gbs": {1: "531ccab08560d17e0cb8315ae124a8cb",
                   2: "a981130cf2b7e09f4686dc273cf7187e"}
           }


class BasicSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Basic Setup
                """)

    def setup(self):
        global dpcsh_obj, target_linux_obj, source_linux_obj

        dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM)
        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']

        dpcsh_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)
        target_linux_obj = Linux(host_ip=target_machine, ssh_username=username, ssh_password=password)
        source_linux_obj = Linux(host_ip=source_machine, ssh_username=username, ssh_password=password)

    def cleanup(self):
        pass


class TestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test LSO with different mss values and various file sizes (SCP)",
                              steps="""
                              1. Set mss values for each file transfer
                              2. SCP files of different file sizes from cadence-pc-3 to cadence-pc-4
                              3. Validate md5sum of each file that is transferred
                              mss values: %s 
                              File Sizes in KBs: %s
                              File Sizes in MBs: %s
                              File Sizes in GBs: %s
                              """ % (mss_values, file_sizes_in_kbs, file_sizes_in_mbs, file_sizes_in_gbs))

    def setup(self):
        pass

    def run(self):
        for mss in mss_values:
            fun_test.log("Setting mss value: %d" % mss)
            mss_set = dpcsh_obj.set_nu_test_op(rule=0, lso=mss)
            fun_test.simple_assert(mss_set, "MSS set")

            # Test for KB files with different mss
            for file_size in file_sizes_in_kbs:
                fun_test.log("Transferring file of %d KB with mss: %d" % (file_size, mss))

                file_path = file_dir + "%dkb" % file_size
                scp_cmd = "ip netns exec n1 scp %s %s@%s:%s" % (file_path, username, target_machine_ip, file_dir)
                source_linux_obj.command(command=scp_cmd, custom_prompts={"password: ": password}, timeout=300)

                checkpoint = "Validating md5sum of the %d KB file " % file_size
                md5sum = target_linux_obj.md5sum(file_name=file_path)
                fun_test.test_assert_expected(expected=md5sums['kbs'][file_size], actual=md5sum, message=checkpoint)

                checkpoint = "Remove all files from target machine"
                target_linux_obj.remove_file(file_name=file_path)
                fun_test.add_checkpoint(checkpoint)

            # Test for MB files with different mss
            for file_size in file_sizes_in_mbs:
                fun_test.log("Transferring file of %d MB with mss: %d" % (file_size, mss))

                file_path = file_dir + "%dmb" % file_size
                scp_cmd = "ip netns exec n1 scp %s %s@%s:%s" % (file_path, username, target_machine_ip, file_dir)
                source_linux_obj.command(command=scp_cmd, custom_prompts={"password: ": password}, timeout=3600)

                checkpoint = "Validating md5sum of the %d MB file " % file_size
                md5sum = target_linux_obj.md5sum(file_name=file_path)
                fun_test.test_assert_expected(expected=md5sums['mbs'][file_size], actual=md5sum, message=checkpoint)

                checkpoint = "Remove all files from target machine"
                target_linux_obj.remove_file(file_name=file_path)
                fun_test.add_checkpoint(checkpoint)

            if mss == 1300:
                # Test for GB files with different mss
                for file_size in file_sizes_in_gbs:
                    fun_test.log("Transferring file of %d GB with mss: %d" % (file_size, mss))

                    file_path = file_dir + "%dgb" % file_size
                    scp_cmd = "ip netns exec n1 scp %s %s@%s:%s" % (file_path, username, target_machine_ip, file_dir)
                    source_linux_obj.command(command=scp_cmd, custom_prompts={"password: ": password}, timeout=1800)

                    checkpoint = "Validating md5sum of the %d GB file " % file_size
                    md5sum = target_linux_obj.md5sum(file_name=file_path)
                    fun_test.test_assert_expected(expected=md5sums['gbs'][file_size], actual=md5sum, message=checkpoint)

                    checkpoint = "Remove all files from target machine"
                    target_linux_obj.remove_file(file_name=file_path)
                    fun_test.add_checkpoint(checkpoint)

            # Delete current rule
            checkpoint = "Delete LSO rule 0 with mss %d" % mss
            rule_deleted = dpcsh_obj.delete_nu_test_op(rule=0)
            fun_test.simple_assert(rule_deleted, checkpoint)

    def cleanup(self):
        fun_test.log("In Test Cleanup")

        checkpoint = "Delete LSO rule 0"
        dpcsh_obj.delete_nu_test_op(rule=0)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Remove all files from target machine"
        files = target_linux_obj.list_files(path=file_dir)
        for file_name in files:
            file_path = file_dir + "%s" % file_name
            target_linux_obj.remove_file(file_name=file_path)
        fun_test.add_checkpoint(checkpoint)


if __name__ == "__main__":
    ts = BasicSetup()
    ts.add_test_case(TestCase1())
    ts.run()
