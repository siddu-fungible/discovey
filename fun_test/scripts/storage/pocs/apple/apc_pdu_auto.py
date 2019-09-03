from apc_pdu_auto_helper import *
from asset.asset_manager import AssetManager
from lib.host.apc_pdu import ApcPdu
import re
from lib.fun.fs import ComE, Bmc
from lib.host.linux import Linux
from lib.topology.topology_helper import TopologyHelper


class ApcPduScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

    def cleanup(self):
        pass


class ApcPduTestcase(FunTestCase):
    NUMBER_OF_ITERATIONS = 2

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test",
                              steps="""
                              1. power down and wait for 5 sec
                              2. power on and wait for 360 seconds.
                              3. Check BMC, COMe, SSd's, ports
                              4. repeat the above steps for given number of iterations
                              """)

    def setup(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        # fs_name = "fs-41"
        self.fs = AssetManager().get_fs_by_name(fs_name)
        self.apc_info = self.fs.get("apc_info", None)
        self.outlet_no = self.apc_info.get("outlet_number", None)

        # if you are loading the image every time you boot up
        self.f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server" \
                              " --dpc-uart --csr-replay --all_100g --nofreeze"
        self.f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server" \
                              " --dpc-uart --csr-replay --all_100g --nofreeze"
        print(json.dumps(self.fs, indent=4))

    def run(self):
        for pc_no in range(self.NUMBER_OF_ITERATIONS):
            self.pc_no = pc_no

            come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                               ssh_username=self.fs['come']['mgmt_ssh_username'],
                               ssh_password=self.fs['come']['mgmt_ssh_password'])
            qa_02_handle = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
            qa_02_handle.destroy()
            come_handle.destroy()

            fun_test.add_checkpoint(checkpoint="ITERATION : {}".format(pc_no))

            fs_reboot = self.apc_pdu_reboot(come_handle)

            fun_test.log("Checking if COMe is UP")
            come_up = come_handle.ensure_host_is_up(max_wait_time=350)
            fun_test.test_assert(come_up, "COMe is UP")

            fun_test.log("Checking if BMC is UP")
            bmc_up = qa_02_handle.ping(dst=self.fs['bmc']['mgmt_ip'])
            fun_test.test_assert(bmc_up, "BMC is UP")
            qa_02_handle.destroy()

            initial = come_handle.command("uptime")
            output = come_handle.command("uptime")
            up_time = re.search(r'(\d+) min', output)
            up_time_less_than_5 = False
            if up_time:
                up_time_min = int(up_time.group(1))
                if up_time_min <= 5:
                    up_time_less_than_5 = True
            fun_test.test_assert(up_time_less_than_5, "COMe 'uptime' less than 5 min")

            come_handle.destroy()
            qa_02_handle.destroy()

            topology_helper = TopologyHelper()
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.f1_0_boot_args},
                                                              1: {"boot_args": self.f1_1_boot_args}},
                                               skip_funeth_come_power_cycle=True,
                                               dut_index=0
                                               )
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology deployed")

            fun_test.log("Checking if SSD's are Active")
            ssd_valid = check_ssd(come_handle, expected_ssds_up=12)
            fun_test.test_assert(ssd_valid, "SSD's ONLINE")

            fun_test.log("Checking if NU and HNU port's are active")
            nu_port_valid_fs_0 = check_nu_ports(come_handle, iteration=pc_no, f1=0,
                                                expected_ports_up={"NU": [0, 4, 8, 12], "HNU": []})
            fun_test.test_assert(nu_port_valid_fs_0, "NU ports are present (0,4,8,12)")

            # Minor checks: docker and cores

            fun_test.log("Checking the Docker")
            come_handle.command("docker ps -a")
            fun_test.log("Checking the cores")
            come_handle.command("ls /opt/fungible/cores")
            come_handle.destroy()

            fun_test.sleep("Sleeping for 10s before next iteration", seconds=10)

    @staticmethod
    def to_str(boolean_data):
        if boolean_data:
            return FunTest.PASSED
        return FunTest.FAILED

    def apc_pdu_reboot(self, come_handle):
        '''
        1. check COMe is up, if up than power off.
        2. check COMe now, if its down tha power on
        :param come_handle:
        :return:
        '''
        result = False
        try:
            fun_test.log("Iteation no: {} out of {}".format(self.pc_no + 1, self.NUMBER_OF_ITERATIONS))

            come_up = come_handle.is_host_up()
            come_handle.destroy()
            fun_test.add_checkpoint("COMe is UP (before powercycle)",
                                    self.to_str(come_up), True, come_up)
            apc_pdu = ApcPdu(host_ip=self.apc_info['host_ip'], username=self.apc_info['username'],
                             password=self.apc_info['password'])
            fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

            apc_outlet_off_msg = apc_pdu.outlet_off(self.outlet_no)
            fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
            outlet_off = self.match_success(apc_outlet_off_msg)
            fun_test.test_assert(outlet_off, "Power down FS")

            fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=5)
            come_down = not (come_handle.is_host_up(max_wait_time=30))
            come_handle.destroy()
            fun_test.test_assert(come_down, "COMe is Down")

            apc_outlet_on_msg = apc_pdu.outlet_on(self.outlet_no)
            fun_test.log("APC PDU outlet on mesg {}".format(apc_outlet_on_msg))
            outlet_on = self.match_success(apc_outlet_on_msg)
            fun_test.test_assert(outlet_on, "Power on FS")

            apc_pdu.disconnect()
            result = True
        except:
            fun_test.log("Error: unable to connect to ApcPdu")

        return result

    def match_success(self, output_message):
        result = False
        match_success = re.search(r'Success', output_message)
        if match_success:
            result = True
        return result

    def cleanup(self):
        pass


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
