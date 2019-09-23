from stimit_apc_pdu_auto_helper import *
from asset.asset_manager import AssetManager
from lib.host.apc_pdu import ApcPdu
import re
from lib.fun.fs import ComE, Bmc, Fpga
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
    NUMBER_OF_ITERATIONS = 100

    def describe(self):
        self.set_test_details(id=1,
                              summary="Powercycle test",
                              steps="""
                                1. Reboot the FS.
                                2. Check if COMe is up, than we check for BMC, FPGA.
                                3. Load the images and bring F1 up.
                                4. now check for SSD's and NU & HNU ports validation. 
                              """)

    def setup(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)
        self.apc_info = self.fs.get("apc_info", None)
        self.outlet_no = self.apc_info.get("outlet_number", None)

        self.validate = {"check_storage_controller": False, "check_ssd": False, "check_ports": False}
        job_inputs = fun_test.get_job_inputs()
        if job_inputs:
            if "iterations" in job_inputs:
                self.NUMBER_OF_ITERATIONS = job_inputs["iterations"]
            if "check_ssd" in job_inputs:
                self.validate["check_ssd"] = job_inputs["check_ssd"]
            if "ports" in job_inputs:
                self.validate["ports"] = job_inputs["check_ports"]
            if "check_storage_controller" in job_inputs:
                self.validate["check_storage_controller"] = job_inputs["check_storage_controller"]
        fun_test.log(json.dumps(self.fs, indent=4))
        fun_test.log(self.validate)

    def run(self):
        '''
        1. Reboot the FS.
        2. Check if COMe is up, than we check for BMC, FPGA.
        3. Load the images and bring F1 up.
        4. now check for SSD's and NU & HNU ports validation.
        :return:
        '''
        for pc_no in range(self.NUMBER_OF_ITERATIONS):
            self.pc_no = pc_no

            come_handle = ComE(host_ip='',
                               ssh_username=self.fs['come']['mgmt_ssh_username'],
                               ssh_password=self.fs['come']['mgmt_ssh_password'])
            bmc_handle = Bmc(host_ip="",
                             ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                             ssh_password=self.fs['bmc']['mgmt_ssh_password'])
            bmc_handle.set_prompt_terminator(r'# $')

            fun_test.add_checkpoint(checkpoint="ITERATION : {}".format(pc_no))

            self.apc_pdu_reboot(come_handle)

            # Destroy any previously opened sessions(i.e After the power cycle)

            come_handle.destroy()

            fun_test.log("Checking if COMe is UP")
            come_up = come_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(come_up, "COMe is UP")

            fun_test.log("Checking if BMC is UP")
            bmc_up = bmc_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(bmc_up, "BMC is UP")

            initial = come_handle.command("uptime")
            output = come_handle.command("uptime")
            up_time = re.search(r'(\d+) min', output)
            up_time_less_than_5 = False
            if up_time:
                up_time_min = int(up_time.group(1))
                if up_time_min <= 5:
                    up_time_less_than_5 = True
            fun_test.test_assert(up_time_less_than_5, "COMe 'up-time' less than 5 min")

            if self.validate["check_storage_controller"]:
                fun_test.log("Checking if storage controller is up")
                timer = FunTimer(max_time=300)
                while not timer.is_expired():
                    output = come_handle.command("curl -I -u admin:password http://10.1.105.141:50220/FunCC/v1/topology")
                    match_status = re.search(r'HTTP/[\d.]+\s+(\d+)', output)
                    if match_status:
                        status = match_status.group(1)
                        if status == "200":
                            break
                    fun_test.sleep("Waiting for storage controller to be up", seconds=10)

                come_handle.command("curl -u admin:password http://10.1.105.141:50220/FunCC/v1/topology | json_pp")

            if self.validate["check_ssd"]:
                fun_test.log("Checking if SSD's are Active on F1_0")
                ssd_valid = check_ssd(come_handle, expected_ssds_up=12, f1=0)
                fun_test.test_assert(ssd_valid, "F1_0: SSD's ONLINE")

                fun_test.log("Checking if SSD's are Active on F1_1")
                ssd_valid = check_ssd(come_handle, expected_ssds_up=12, f1=1)
                fun_test.test_assert(ssd_valid, "F1_1: SSD's ONLINE")

            if self.validate["check_ports"]:
                fun_test.log("Checking if NU and HNU port's are active")
                nu_port_valid = check_nu_ports(come_handle, iteration=pc_no, f1=0, expected_ports_up={'NU': range(8),
                                                                                                      'HNU': []})
                fun_test.test_assert(nu_port_valid, "F1_0: NU ports are present")

                fun_test.log("Checking if NU and HNU port's are active on F1_1")
                nu_port_valid = check_nu_ports(come_handle, iteration=pc_no, f1=1, expected_ports_up={'NU': range(8),
                                                                                                      'HNU': []})
                fun_test.test_assert(nu_port_valid, "F1_1: NU ports are present")

            # Minor checks: docker and cores

            fun_test.log("Checking the Docker")
            come_handle.command("docker ps -a")
            fun_test.log("Checking the cores")
            come_handle.command("ls /opt/fungible/cores")

            come_handle.destroy()
            bmc_handle.destroy()

            fun_test.sleep("Sleeping for 10s before next iteration", seconds=10)

    def apc_pdu_reboot(self, come_handle):
        '''
        1. check if COMe is up, than power off.
        2. check COMe now, if its down tha power on
        :param come_handle:
        :return:
        '''
        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.NUMBER_OF_ITERATIONS))

        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        apc_pdu = ApcPdu(host_ip=self.apc_info['host_ip'], username=self.apc_info['username'],
                         password=self.apc_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

        apc_outlet_off_msg = apc_pdu.outlet_off(self.outlet_no)
        fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
        outlet_off = self.match_success(apc_outlet_off_msg)
        fun_test.test_assert(outlet_off, "Power down FS")

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=5)

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=30))
        fun_test.test_assert(come_down, "COMe is Down")
        come_handle.destroy()

        apc_outlet_on_msg = apc_pdu.outlet_on(self.outlet_no)
        fun_test.log("APC PDU outlet on message {}".format(apc_outlet_on_msg))
        outlet_on = self.match_success(apc_outlet_on_msg)
        fun_test.test_assert(outlet_on, "Power on FS")

        apc_pdu.disconnect()

        return

    @staticmethod
    def match_success(output_message):
        result = False
        match_success = re.search(r'Success', output_message)
        if match_success:
            result = True
        return result

    @staticmethod
    def to_str(boolean_data):
        if boolean_data:
            return FunTest.PASSED
        return FunTest.FAILED

    def cleanup(self):
        pass


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
