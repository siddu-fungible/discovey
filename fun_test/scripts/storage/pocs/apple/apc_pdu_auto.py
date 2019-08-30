from apc_pdu_auto_helper import *
from asset.asset_manager import AssetManager
from lib.host.apc_pdu import ApcPdu
import re
from lib.fun.fs import ComE, Bmc
from lib.host.linux import Linux


class ApcPduScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

    def cleanup(self):
        pass


class ApcPduTestcase(FunTestCase):
    NUMBER_OF_ITERATIONS = 30

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
        fs_47 = {
            "name": "fs-47",
            "gateway_ip": "10.1.105.1",
            "bmc": {
                "mgmt_ip": "10.1.105.53",
                "mgmt_ssh_username": "sysadmin",
                "mgmt_ssh_password": "superuser"
            },
            "fpga": {
                "mgmt_ip": "10.1.105.56",
                "mgmt_ssh_username": "root",
                "mgmt_ssh_password": "root"
            },
            "come": {
                "mgmt_ip": "10.1.105.58",
                "mgmt_ssh_username": "fun",
                "mgmt_ssh_password": "123"
            },
            "apc_info": {
                "host_ip": "10.1.105.247",
                "username": "localadmin",
                "password": "Precious1*"
            },
            "outlet_number": 15
        }

        # fs_name = fun_test.get_job_environment_variable("test_bed_type")
        # self.fs = AssetManager().get_fs_by_name(fs_name)
        self.fs = fs_47
        self.apc_info = self.fs.get("apc_info", None)
        self.outlet_no = self.fs.get("outlet_number", None)
        print(json.dumps(self.fs, indent=4))

    def run(self):
        for pc_no in range(self.NUMBER_OF_ITERATIONS):
            try:
                self.pc_no = pc_no
                while True:
                    result = self.apc_pdu_reboot()
                    if result:
                        break
                    fun_test.sleep("sleeping for 300 sec before next try", seconds=300)

                fun_test.add_checkpoint(checkpoint="ITERATION : {}".format(pc_no))

                fun_test.log("Checking if BMC is UP")
                qa_02_handle = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
                bmc_up = qa_02_handle.ping(dst=self.fs['bmc']['mgmt_ip'])
                fun_test.add_checkpoint("BMC is UP",
                                        self.to_str(bmc_up), True, bmc_up)
                qa_02_handle.destroy()

                fun_test.log("Checking if COMe is UP")
                come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                   ssh_username=self.fs['come']['mgmt_ssh_username'],
                                   ssh_password=self.fs['come']['mgmt_ssh_password'])
                come_up = come_handle.is_host_up()
                fun_test.add_checkpoint("COMe is UP",
                                        self.to_str(come_up), True, come_up)

                fun_test.log("Checking if SSD's are Active")
                ssd_valid = check_ssd(come_handle, expected_ssds_up=6)
                fun_test.add_checkpoint("SSD's ONLINE",
                                        self.to_str(ssd_valid), True, ssd_valid)

                fun_test.log("Checking if NU and HNU port's are active")
                nu_port_valid_fs_0 = check_nu_ports(come_handle, iteration=pc_no, f1=0,
                                                    expected_ports_up={"NU": range(24), "HNU": []})
                fun_test.add_checkpoint("NU ports are present (0-23)",
                                        self.to_str(nu_port_valid_fs_0), True, nu_port_valid_fs_0)

                # Minor checks: docker and cores

                fun_test.log("Checking the Docker")
                come_handle.command("docker ps -a")
                fun_test.log("Checking the cores")
                come_handle.command("ls /opt/fungible/cores")
                come_handle.destroy()
            except:
                fun_test.log("Error in running the iteration: {}".format(self.pc_no))

            fun_test.sleep("Sleeping for 10s before next iteration", seconds=10)

    @staticmethod
    def to_str(boolean_data):
        if boolean_data:
            return FunTest.PASSED
        return FunTest.FAILED

    def apc_pdu_reboot(self):
        result = False
        try:
            fun_test.log("Iteation no: {} out of {}".format(self.pc_no + 1, self.NUMBER_OF_ITERATIONS))
            apc_pdu = ApcPdu(host_ip=str(self.apc_info['host_ip']), username=str(self.apc_info['username']),
                             password=str(self.apc_info['password']))
            fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

            apc_outlet_off_msg = apc_pdu.outlet_off(self.outlet_no)
            fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
            fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=5)

            apc_outlet_on_msg = apc_pdu.outlet_on(self.outlet_no)
            fun_test.log("APC PDU outlet on mesg {}".format(apc_outlet_on_msg))
            fun_test.sleep(message="Wait for few seconds after switching on fs outlet", seconds=5)

            apc_outlet_status_msg = apc_pdu.outlet_status(self.outlet_no)

            outlet_status = re.search(r"^olStatus.*Outlet\s+{}\s+.*(ON|OFF)".format(str(self.outlet_no)),
                                      apc_outlet_status_msg, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            fun_test.simple_assert(expression=outlet_status.groups()[0] == 'On', context=None,
                                   message="Power did not come back after pdu port reboot")

            fun_test.sleep(message="Wait for 360 seconds before Checking if platform components are up", seconds=360)
            apc_pdu.disconnect()
            result = True
        except:
            fun_test.log("Error: unable to connect to ApcPdu")

        return result

    def cleanup(self):
        pass


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
