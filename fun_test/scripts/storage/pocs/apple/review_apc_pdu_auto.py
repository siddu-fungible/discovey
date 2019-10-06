from scripts.storage.pocs.apple.apc_pdu_auto_helper import *
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
    END_SLEEP = 300
    DOCKER_VERIFY_INTERVAL = 60
    AFTER_RUNSC_UP_HOST_CONNECT_INTERVAL = 60

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
        self.fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(self.fs_name)
        self.apc_info = self.fs.get("apc_info", None)
        self.outlet_no = self.apc_info.get("outlet_number", None)
        self.validate = {"check_storage_controller": False,
                         "check_ssd": False,
                         "check_ports": False,
                         "expected_ssds_f1_0": 12,
                         "expected_ssds_f1_1": 12,
                         "expected_nu_ports_f1_0": range(0, 24, 4),
                         "expected_nu_ports_f1_1": range(0, 24, 4),
                         "expected_hnu_ports_f1_0": [],
                         "expected_hnu_ports_f1_1": [],
                         "hosts": {},
                         "check_docker": False,
                         "expected_dockers": 3,
                         "target_ip": "15.53.1.2"
                         }
        job_inputs = fun_test.get_job_inputs()
        if job_inputs:
            if "iterations" in job_inputs:
                self.NUMBER_OF_ITERATIONS = job_inputs["iterations"]
            if "check_ssd" in job_inputs:
                self.validate["check_ssd"] = job_inputs["check_ssd"]
            if "check_ports" in job_inputs:
                self.validate["check_ports"] = job_inputs["check_ports"]
            if "expected_ssds_f1_0" in job_inputs:
                self.validate["expected_ssds_f1_0"] = job_inputs["expected_ssds_f1_0"]
            if "expected_ssds_f1_1" in job_inputs:
                self.validate["expected_ssds_f1_1"] = job_inputs["expected_ssds_f1_1"]
            if "expected_nu_ports_f1_0" in job_inputs:
                self.validate["expected_nu_ports_f1_0"] = job_inputs["expected_nu_ports_f1_0"]
            if "expected_nu_ports_f1_1" in job_inputs:
                self.validate["expected_nu_ports_f1_1"] = job_inputs["expected_nu_ports_f1_1"]
            if "expected_hnu_ports_f1_0" in job_inputs:
                self.validate["expected_hnu_ports_f1_0"] = job_inputs["expected_hnu_ports_f1_0"]
            if "expected_hnu_ports_f1_1" in job_inputs:
                self.validate["expected_hnu_ports_f1_1"] = job_inputs["expected_hnu_ports_f1_1"]
            if "hosts" in job_inputs:
                self.validate["hosts"] = job_inputs["hosts"]
            if "check_docker" in job_inputs:
                self.validate["check_docker"] = job_inputs["check_docker"]
            if "expected_dockers" in job_inputs:
                self.validate["expected_dockers"] = job_inputs["expected_dockers"]
            if "target_ip" in job_inputs:
                self.validate["target_ip"] = job_inputs["target_ip"]
            if "end_sleep" in job_inputs:
                self.END_SLEEP = job_inputs["end_sleep"]
            if "docker_verify_interval" in job_inputs:
                self.DOCKER_VERIFY_INTERVAL = job_inputs["docker_verify_interval"]
            if "after_runsc_up_host_connect_interval" in job_inputs:
                self.AFTER_RUNSC_UP_HOST_CONNECT_INTERVAL = job_inputs["after_runsc_up_host_connect_interval"]

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

            come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                               ssh_username=self.fs['come']['mgmt_ssh_username'],
                               ssh_password=self.fs['come']['mgmt_ssh_password'])
            bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
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

            # Check if lspci devices are detected
            lspci_f0 = check_pci_dev(come_handle, f1=0)
            fun_test.test_assert(lspci_f0, "F1_0 PCIe devices not detected")

            lspci_f1 = check_pci_dev(come_handle, f1=1, fs_name=self.fs_name)
            fun_test.test_assert(lspci_f1, "F1_1 PCIe devices not detected")

            check_come_up_time(come_handle, expected_seconds=5)

            if self.validate["check_ssd"]:
                fun_test.log("Checking if SSD's are Active on F1_0")
                check_ssd(come_handle,
                          expected_ssds_up=self.validate["expected_ssds_f1_0"],
                          f1=0)

                fun_test.log("Checking if SSD's are Active on F1_1")
                check_ssd(come_handle,
                          expected_ssds_up=self.validate["expected_ssds_f1_1"],
                          f1=1)

            if self.validate["check_ports"]:
                fun_test.log("Checking if NU and HNU port's are active on F1_0")
                expected_ports_up_f1_0 = {'NU': self.validate["expected_nu_ports_f1_0"],
                                          'HNU': self.validate["expected_hnu_ports_f1_0"]}
                nu_port_valid = check_nu_ports(come_handle, iteration=pc_no, f1=0,
                                               expected_ports_up=expected_ports_up_f1_0)
                fun_test.test_assert(nu_port_valid, "F1_0: NU ports are present, Expected: {}".format(expected_ports_up_f1_0))
                expected_ports_up_f1_1 = {'NU': self.validate["expected_nu_ports_f1_1"],
                                          'HNU': self.validate["expected_hnu_ports_f1_1"]}
                fun_test.log("Checking if NU and HNU port's are active on F1_1")
                nu_port_valid = check_nu_ports(come_handle, iteration=pc_no, f1=1,
                                               expected_ports_up=expected_ports_up_f1_1)
                # fun_test.test_assert(nu_port_valid, "F1_1: NU ports are present, Expected: {}".format(expected_ports_up_f1_1))
                if nu_port_valid:
                    fun_test.add_checkpoint("F1_1: NU ports are present, Expected: {}".
                                            format(expected_ports_up_f1_1), "PASSED")
                else:
                    fun_test.add_checkpoint("F1_1: NU ports are present, Expected: {}".
                                            format(expected_ports_up_f1_1), "FAILED")

            if self.validate["check_docker"]:
                fun_test.sleep("docker to be up", seconds=self.DOCKER_VERIFY_INTERVAL)
                check_docker(come_handle, expected=self.validate["expected_dockers"])

            # Todo: remove for loop in the helper script (previously had codded to work parallelly with multiple host,
            #  now we have to do it serially, so no need of for loops in helper function)
            if self.validate["hosts"]:
                fun_test.sleep("Hosts to be up", seconds=self.AFTER_RUNSC_UP_HOST_CONNECT_INTERVAL)
                hosts_list = get_hosts_handle(self.validate["hosts"])
                for host_name, host in hosts_list.iteritems():
                    single_host = {host_name: host}
                    connect_the_host(single_host, self.validate["target_ip"])
                    host["nvme"] = get_nvme(single_host)
                    # Start traffic
                    run_traffic_bg(single_host)
                    # Check if traffic is running
                    check_traffic(single_host)
                    # Disconnect volume
                    disconnect_vol(single_host, self.validate["target_ip"])
                    destroy_hosts_handle(single_host)
            come_handle.destroy()
            bmc_handle.destroy()

            fun_test.sleep("before next iteration", seconds=self.END_SLEEP)

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

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=30)

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
