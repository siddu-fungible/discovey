from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.apc_pdu import ApcPdu
import re
import urllib
from lib.fun.fs import ComE, Bmc, Fpga
from lib.system import utils
from lib.host.linux import Linux
from collections import OrderedDict
import requests
from lib.templates.storage.storage_controller_api import StorageControllerApi
from lib.topology.topology_helper import TopologyHelper
import dlipower
from lib.fun.fs import Fs


class ApcPduScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

    def wipe_out_cassandra_es_database(self):
        self.come_handle.command("cd /var/opt/fungible")
        self.come_handle.sudo_command("rm -r elasticsearch")
        self.come_handle.sudo_command("rm -r cassandra")

    def restart_fs1600(self):
        self.come_handle.command("cd /opt/fungible/etc")
        self.come_handle.command("bash ResetFs1600.sh")

    def cleanup(self):
        pass


class ApcPduTestcase(FunTestCase):
    VOL_NAME = "Stripe"

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
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)
        if self.testbed_type != "suite_based":
            self.fs = AssetManager().get_fs_spec(self.testbed_type)
            fun_test.log(json.dumps(self.fs, indent=4))

        self.topology_helper = TopologyHelper()
        self.topology_helper.set_dut_parameters(dut_index=0,
                                                f1_parameters={0: {"boot_args": Fs.DEFAULT_BOOT_ARGS},
                                                               1: {"boot_args": Fs.DEFAULT_BOOT_ARGS}},
                                                fs_parameters={"already_deployed": True})

        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict.iteritems():
            setattr(self, k, v)

        job_inputs = fun_test.get_job_inputs()
        if job_inputs:
            if "iterations" in job_inputs:
                self.iterations = job_inputs["iterations"]
            if "check_ssd" in job_inputs:
                self.check_ssd = job_inputs["check_ssd"]
            if "check_ports" in job_inputs:
                self.check_ports = job_inputs["check_ports"]
            if "expected_ssds_f1_0" in job_inputs:
                self.expected_ssds_f1_0 = job_inputs["expected_ssds_f1_0"]
            if "expected_ssds_f1_1" in job_inputs:
                self.expected_ssds_f1_1 = job_inputs["expected_ssds_f1_1"]
            if "expected_nu_ports_f1_0" in job_inputs:
                self.expected_nu_ports_f1_0 = job_inputs["expected_nu_ports_f1_0"]
            if "expected_nu_ports_f1_1" in job_inputs:
                self.expected_nu_ports_f1_1 = job_inputs["expected_nu_ports_f1_1"]
            if "expected_hnu_ports_f1_0" in job_inputs:
                self.expected_hnu_ports_f1_0 = job_inputs["expected_hnu_ports_f1_0"]
            if "expected_hnu_ports_f1_1" in job_inputs:
                self.expected_hnu_ports_f1_1 = job_inputs["expected_hnu_ports_f1_1"]
            if "num_hosts" in job_inputs:
                self.num_hosts = job_inputs["num_hosts"]
            if "check_docker" in job_inputs:
                self.check_docker = job_inputs["check_docker"]
            if "expected_dockers" in job_inputs:
                self.expected_dockers = job_inputs["expected_dockers"]
            if "target_ip" in job_inputs:
                self.target_ip = job_inputs["target_ip"]
            if "end_sleep" in job_inputs:
                self.end_sleep = job_inputs["end_sleep"]
            if "after_runsc_up_host_connect_interval" in job_inputs:
                self.after_runsc_up_host_connect_interval = job_inputs["after_runsc_up_host_connect_interval"]
            if "check_portal" in job_inputs:
                self.check_portal = job_inputs["check_portal"]
            if "apc_pdu_power_cycle" in job_inputs:
                self.apc_pdu_power_cycle_test = job_inputs["apc_pdu_power_cycle"]
            if "reboot_machine_test" in job_inputs:
                self.reboot_machine_test = job_inputs["reboot_machine_test"]
            if "reset_f1s_bmc" in job_inputs:
                self.reset_f1s_bmc = job_inputs["reset_f1s_bmc"]


    def run(self):
        '''
        1. Reboot the FS.
        2. Check if COMe is up, than we check for BMC, FPGA.
        3. Load the images and bring F1 up.
        4. now check for SSD's and NU & HNU ports validation.
        :return:
        '''

        for pc_no in range(self.iterations):
            self.pc_no = pc_no

            fun_test.add_checkpoint(checkpoint="ITERATION : {} out of {}".format(pc_no + 1, self.iterations))


            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])
            self.bmc_handle.set_prompt_terminator(r'# $')

            self.reboot_test()
            self.come_handle.destroy()
            self.bmc_handle.destroy()

            self.basic_checks()
            self.data_integrity_check()

            self.come_handle.destroy()
            self.bmc_handle.destroy()
            self.come_handle.destroy()
            self.bmc_handle.destroy()

            fun_test.sleep("before next iteration", seconds=self.end_sleep)

    def basic_checks(self):
        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])
        self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                              ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                              ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                              bundle_compatible=True)
        self.bmc_handle.set_prompt_terminator(r'# $')

        fun_test.log("Checking if COMe is UP")
        come_up = self.come_handle.ensure_host_is_up(max_wait_time=600)
        fun_test.test_assert(come_up, "COMe is UP")

        fun_test.log("Checking if BMC is UP")
        bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=600)
        fun_test.test_assert(bmc_up, "BMC is UP")

        if self.reboot_machine_test or self.apc_pdu_power_cycle_test:
            self.check_come_up_time(expected_minutes=5)

        # topology = self.topology_helper.deploy()
        # self.fs_obj = topology.get_dut_instance(index=0)
        # self.dpc_f1_0 = self.fs_obj.get_dpc_client(0)
        # self.dpc_f1_1 = self.fs_obj.get_dpc_client(1)
        if self.check_docker:
            self.check_expected_dockers_up()

        if self.check_portal:
            self.check_portal_up()

        # Check if lspci devices are detected
        fun_test.log("Check if F1_0 is detected")
        self.check_pci_dev(f1=0)

        fun_test.log("Check if F1_1 is detected")
        self.check_pci_dev(f1=1)

        if self.check_ssd:
            fun_test.log("Checking if SSD's are Active on F1_0")
            self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_0, f1=0)

            fun_test.log("Checking if SSD's are Active on F1_1")
            self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_1, f1=1)

        if self.check_ports:
            fun_test.log("Checking if NU and HNU port's are active on F1_0")
            expected_ports_up_f1_0 = {'NU': self.expected_nu_ports_f1_0,
                                      'HNU': self.expected_hnu_ports_f1_0}
            self.get_dpcsh_data_for_cmds("port enableall", f1=0)
            fun_test.sleep("Before checking port status", seconds=40)
            self.check_nu_ports(f1=0, expected_ports_up=expected_ports_up_f1_0)

            expected_ports_up_f1_1 = {'NU': self.expected_nu_ports_f1_1,
                                      'HNU': self.expected_hnu_ports_f1_1}
            fun_test.log("Checking if NU and HNU port's are active on F1_1")
            self.get_dpcsh_data_for_cmds("port enableall", f1=1)
            fun_test.sleep("Before checking port status", seconds=40)
            self.check_nu_ports(f1=1, expected_ports_up=expected_ports_up_f1_1)

    def data_integrity_check(self):
        if self.num_hosts:
            fun_test.sleep("Wait for GUI to come up", seconds=80)
            self.sc_api = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'],
                                               api_server_port=self.api_server_port,
                                               username=self.username,
                                               password=self.password)
            if self.pc_no == 0:
                required_hosts_list = self.verify_and_get_required_hosts_list(self.num_hosts)
                self.pool_uuid = self.get_pool_id()
                self.volume_uuid_details = self.create_vol(self.num_hosts)
                self.attach_volumes_to_host(required_hosts_list)
                self.get_host_handles()
                self.intialize_the_hosts()
            else:
                self.get_host_handles()
            self.connect_the_host_to_volumes()
            self.verify_nvme_connect()
            self.start_fio_and_verify(required_hosts_list)
            self.disconnect_the_hosts()
            self.destoy_host_handles()

    def reboot_test(self):
        pdu_type = self.fs.get("pdu_type", "apc")
        if self.reboot_machine_test:
            self.reboot_fs1600()
        elif self.apc_pdu_power_cycle_test:
            if pdu_type == "apc":
                self.apc_pdu_reboot()
            elif pdu_type == "dli":
                self.dli_pdu_reboot()
        elif self.reset_f1s_bmc:
            self.reset_f1s_bmc_test()

    def apc_pdu_reboot(self):
        '''
        1. check if COMe is up, than power off.
        2. check COMe now, if its down tha power on
        :param come_handle:
        :return:
        '''
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        apc_info = self.fs.get("apc_info")
        outlet_no = apc_info.get("outlet_number")

        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))

        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        apc_pdu = ApcPdu(host_ip=apc_info['host_ip'], username=apc_info['username'],
                         password=apc_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

        apc_outlet_off_msg = apc_pdu.outlet_off(outlet_no)
        fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
        outlet_off = self.match_success(apc_outlet_off_msg)
        fun_test.test_assert(outlet_off, "Power down FS")

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
        fun_test.test_assert(come_down, "COMe is Down")

        apc_outlet_on_msg = apc_pdu.outlet_on(outlet_no)
        fun_test.log("APC PDU outlet on message {}".format(apc_outlet_on_msg))
        outlet_on = self.match_success(apc_outlet_on_msg)
        fun_test.test_assert(outlet_on, "Power on FS")

        come_handle.destroy()
        apc_pdu.disconnect()
        return

    def dli_pdu_reboot(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        dli_info = self.fs.get("dli_info")
        outlet_no = dli_info.get("outlet_number")

        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))

        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        dli_pdu = DliPower(hostname=dli_info['host_ip'], userid=dli_info['username'], password=dli_info['password'])


        dli_outlet_off_result = dli_pdu.outlet_off(outlet_no)
        fun_test.log("DLI PDU outlet off result: {}".format(dli_outlet_off_result))
        fun_test.test_assert(dli_outlet_off_result, "Power down FS")

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
        fun_test.test_assert(come_down, "COMe is Down")

        dli_outlet_on_result = dli_pdu.outlet_on(outlet_no)
        fun_test.log("DLI PDU outlet on message {}".format(dli_outlet_on_result))
        fun_test.test_assert(dli_outlet_on_result, "Power on FS")

        return

    def reset_f1s_bmc_test(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])

        try:
            fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))
            fun_test.log("Checking if COMe is UP")
            come_up = come_handle.ensure_host_is_up()
            fun_test.add_checkpoint("COMe is UP (before resettign F1s)",
                                    self.to_str(come_up), True, come_up)

            come_handle.sudo_command("/opt/fungible/cclinux/cclinux_service.sh --stop")

            bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                             ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                             ssh_password=self.fs['bmc']['mgmt_ssh_password'])

            bmc_handle.command("cd /mnt/sdmmc0p1/scripts; ./REV2_f1_reset.sh 0")
            bmc_handle.command("cd /mnt/sdmmc0p1/scripts; ./REV2_f1_reset.sh 1")
            fun_test.sleep(message="Wait for F1s to reset", seconds=45)

            come_handle.reboot()

            fun_test.log("Checking if COMe is UP")
            come_up = come_handle.ensure_host_is_up()
            fun_test.add_checkpoint("COMe is UP (before resettign F1s)",
                                    self.to_str(come_up), True, come_up)

            fun_test.sleep(message="Wait for Containers to come up", seconds=45)

            bmc_handle.destroy()
            come_handle.destroy()
        except Exception as ex:
            fun_test.critical(ex)

        return

    def reboot_fs1600(self):
        self.wipe_out_cassandra_es_database()
        come_down = False
        for i in range(2):
            self.run_reboot_script()
            fun_test.log("Checking if COMe is down")
            come_down = self.ensure_host_is_down(max_wait_time=60)
            if come_down:
                break
        fun_test.test_assert(come_down, "COMe is Down")
        self.come_handle.destroy()

    def run_reboot_script(self):
        self.come_handle.enter_sudo()
        self.come_handle.command("cd /opt/fungible/etc")
        pid = self.come_handle.start_bg_process("bash ResetFs1600.sh")
        fun_test.log("Checking if the reboot is initiated")
        rebooted = True if pid else False

    def ensure_host_is_down(self, max_wait_time):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        if service_host_spec:
            service_host = Linux(**service_host_spec)
        else:
            fun_test.log("Regression service host could not be instantiated", context=self.context)

        max_down_timer = FunTimer(max_time=max_wait_time)
        result = False
        ping_result = True
        while ping_result and not max_down_timer.is_expired():
            if service_host and ping_result:
                ping_result = service_host.ping(dst=self.fs['come']['mgmt_ip'], count=5)
        if not ping_result:
            result = True
        return result

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

    def check_pci_dev(self, f1=0):
        result = True
        bdf_list = ['04:00.']
        if f1 == 1:
            bdf_list = ['06:00.', '05:00.']
        for bdf in bdf_list:
            lspci_output = self.come_handle.command("lspci -d 1dad: | grep {}".format(bdf), timeout=120)
            if lspci_output:
                sections = ['Ethernet controller', 'Non-Volatile', 'Unassigned class', 'encryption device']
                result = all([s in lspci_output for s in sections])
                if result:
                    break
            else:
                result = False

        fun_test.test_assert(result, "F1_{} PCIe devices detected".format(f1))
        return result

    def check_ssd_status(self, expected_ssds_up, f1=0):
        result = False
        if expected_ssds_up == 0:
            return True
        dpcsh_data = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1)
        if dpcsh_data:
            validate = self.validate_ssd_status(dpcsh_data, expected_ssds_up, f1)
            if validate:
                result = True
        fun_test.test_assert(result, "F1_{}: SSD's ONLINE".format(f1))
        return result

    # def get_dpcsh_data_for_cmds(self, cmd, f1=0):
    #     split_cmd = cmd.split(" ")
    #     verb = split_cmd[0]
    #     data = split_cmd[1]
    #     if f1 == 0:
    #         output = self.dpc_f1_0.json_execute(verb=verb, data=data)
    #     elif f1 == 1:
    #         output = self.dpc_f1_1.json_execute(verb=verb, data=data)
    #     result = output["data"]
    #     return result

    def get_dpcsh_data_for_cmds(self, cmd, f1=0):
        result = False
        try:
            self.come_handle.enter_sudo()
            output = self.come_handle.command("cd /opt/fungible/FunSDK/bin/Linux/dpcsh")
            if "No such file" in output:
                self.come_handle.command("cd /tmp/workspace/FunSDK/bin/Linux")
            run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
            output = self.come_handle.command(run_cmd)
            result = self.parse_dpcsh_output(output)
            self.come_handle.exit_sudo()
        except:
            fun_test.log("Unable to get the DPCSH data for command: {}".format(cmd))
        return result

    @staticmethod
    def parse_dpcsh_output(data):
        result = {}
        data = data.replace('\r', '')
        data = data.replace('\n', '')
        # \s+=>\s+(?P<json_output>{.*})
        match_output = re.search(r'output\s+=>\s+(?P<json_output>{.*})', data)
        if match_output:
            try:
                result = json.loads(match_output.group('json_output'))
                if "result" in result:
                    result = result["result"]
            except:
                fun_test.log("Unable to parse the output obtained from dpcsh")
        return result

    @staticmethod
    def validate_ssd_status(dpcsh_data, expected_ssd_count, f1):
        result = True
        if dpcsh_data:
            ssds_count = len(dpcsh_data)
            fun_test.test_assert_expected(expected=expected_ssd_count,
                                          actual=ssds_count,
                                          message="F1_{}: SSD count".format(f1))
            for each_ssd, value in dpcsh_data.iteritems():
                if "device state" in value:
                    if not (value["device state"] == "DEV_ONLINE"):
                        result = False
        return result

    def check_nu_ports(self,
                       expected_ports_up=None,
                       f1=0):
        result = False
        dpcsh_output = self.get_dpcsh_data_for_cmds("port linkstatus", f1)
        if dpcsh_output:
            ports_up = self.validate_link_status_out(dpcsh_output,
                                                     f1=f1,
                                                     expected_port_up=expected_ports_up)
            if ports_up:
                result = True
        fun_test.test_assert(result, "F1_{}: NU ports are present, Expected: {}".format(f1, expected_ports_up))
        return result

    def validate_link_status_out(self, link_status_out, expected_port_up, f1=0):
        result = True
        link_status = self.parse_link_status_out(link_status_out, f1=f1, iteration=self.pc_no + 1)
        if link_status:
            for port_type, ports_list in expected_port_up.iteritems():
                for each_port in ports_list:
                    port_details = self.get_dict_for_port(port_type, each_port, link_status)
                    if not (port_details["xcvr"] == "PRESENT" and port_details["SW"] == 1 and port_details["HW"] == 1):
                        fun_test.log("Failed to validate the following port details: {}".format(port_details))
                        result = False
                        break
                if not result:
                    break
        else:
            result = False
        return result

    def get_dict_for_port(self, port_type, port, link_status):
        result = {}
        for lport, value in link_status.iteritems():
            if port_type == value.get("type", "") and port == value.get("port", ""):
                result = value
                break
        return result



    @staticmethod
    def parse_link_status_out(link_status_output,
                              f1=0,
                              create_table=True,
                              iteration=1):
        result = OrderedDict()
        if link_status_output:
            port_list = [i for i in link_status_output]
            port_list.sort()
            table_data_rows = []
            for each_port in port_list:
                value = link_status_output[each_port]
                each_port = each_port.replace(' ', '')
                try:
                    match_fields = re.search(r'\s?(?P<name>.*)\s+xcvr:(?P<xcvr>\w+)\s+speed:\s+(?P<speed>\w+)\s+'
                                             r'admin:\s{0,10}(?P<admin>[\w ]+)\s+SW:\s+(?P<sw>\d+)\s+HW:\s+(?P<hw>\d+)\s+'
                                             r'LPBK:\s+(?P<lpbk>\d+)\s+FEC:\s+(?P<fec>\d+)', value)
                    if match_fields:
                        one_data_set = {}
                        one_data_set['name'] = match_fields.group('name').replace(' ', '')
                        if "FPG" in one_data_set['name']:
                            one_data_set['type'] = "HNU" if "HNU" in one_data_set['name'] else "NU"
                        one_data_set['port'] = int(re.search(r'\d+', one_data_set['name']).group())
                        one_data_set['xcvr'] = match_fields.group('xcvr')
                        one_data_set['speed'] = match_fields.group('speed')
                        one_data_set['admin'] = match_fields.group('admin')
                        one_data_set['SW'] = int(match_fields.group('sw'))
                        one_data_set['HW'] = int(match_fields.group('hw'))
                        one_data_set['LPBK'] = match_fields.group('lpbk')
                        one_data_set['FEC'] = match_fields.group('fec')
                        table_data_rows.append([one_data_set['name'], one_data_set['xcvr'], one_data_set['speed'],
                                                one_data_set['admin'], one_data_set['SW'], one_data_set['HW'],
                                                one_data_set['LPBK'], one_data_set['FEC']])
                        result[each_port] = one_data_set
                except:
                    fun_test.log("Unable to parse the port linkstatus output")
            if create_table:
                try:
                    table_data_headers = ["Name", "xcvr", "speed", "admin", "sw", "hw", "lpbk", "fec"]
                    table_data = {"headers": table_data_headers, "rows": table_data_rows}
                    fun_test.add_table(panel_header="Link stats table iteration {}".format(iteration),
                                       table_name="Fs = {}".format(f1), table_data=table_data)
                except:
                    fun_test.log("Unable to create the table")
        return result

    @staticmethod
    def get_name_xcvr(parsed_output):
        result = {}
        if parsed_output:
            for each_port, value in parsed_output.iteritems():
                result[value['name']] = value['xcvr']
        return result

    def get_docker_count(self):
        output = self.come_handle.sudo_command("docker ps -a")
        num_docker = self.docker_ps_a_wrapper(output)
        return num_docker

    @staticmethod
    def docker_ps_a_wrapper(output):
        # Just a basic function , will have to advance it using regex
        lines = output.split("\n")
        lines.pop(0)
        number_of_dockers = len(lines)
        print ("number_of_dockers: %s" % number_of_dockers)
        return number_of_dockers

    def get_hosts_handle(self):
        result = {}
        for host_name, nqn in self.hosts.iteritems():
            host_info = self.hosts_asset[host_name]
            host_handle = Linux(host_ip=host_info['host_ip'],
                                ssh_username=host_info['ssh_username'],
                                ssh_password=host_info['ssh_password'])
            result[host_name] = {"nqn": nqn,
                                 "handle": host_handle}
        return result

    def connect_the_host_to_volumes(self, retry=3):
        for host_name, host_info in self.host_details.iteritems():
            # Try connecting nvme 3 times with an interval of 10 seconds each try, try 5 times
            for iter in range(retry):
                fun_test.log("Trying to connect to nvme, Iteration no: {} out of {}".format(iter + 1, retry))
                nqn = host_info["data"]["subsys_nqn"]
                target_ip = host_info["data"]["ip"]
                remote_ip = host_info["data"]["remote_ip"]
                remote_ip = "nqn.2015-09.com.fungible:" + remote_ip
                result = host_info["handle"].nvme_connect(target_ip=target_ip,
                                                          nvme_subsystem=nqn,
                                                          nvme_io_queues=16,
                                                          retries=5,
                                                          timeout=100,
                                                          hostnqn=remote_ip)
                if result:
                    break
                fun_test.sleep("Before next iteration", seconds=10)

            fun_test.test_assert(result,
                                 "Host: {} nqn: {} connected to DataplaneIP: {}".format(host_name, nqn, target_ip))

    @staticmethod
    def get_nvme(hosts_list):
        result = False
        nvme = ""
        for host_name, host in hosts_list.iteritems():
            output_lsblk = host["handle"].sudo_command("nvme list")
            match_nvme_number = re.search(r'/dev/nvme(\w+)', output_lsblk)
            name = host_name
            if match_nvme_number:
                result = True
                nvme_number = match_nvme_number.group(1)
                nvme = "/dev/nvme" + nvme_number

        fun_test.test_assert(result, "{} host is connected".format(name))
        return nvme

    def check_traffic(self, host_name, fio_run_time, interval=10):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        device = self.host_details[host_name]["nvme"]
        device_name = device.replace("/dev/", '')
        num_list = re.findall(r'\d+', device_name)
        c2 = "c0n" if num_list[0] == "0" else "c2n"
        device_name = "nvme" + num_list[0] + c2 + num_list[1]
        count = fio_run_time / interval
        output_iostat = host_handle.iostat(device=device_name, interval=interval, count=count, background=False)
        self.ensure_io_running(device_name, output_iostat, host_name)
        # fun_test.log(host_handle.command("cat /tmp/{}_fio.txt".format(host_name)))

    @staticmethod
    def ensure_io_running(device, output_iostat, host_name):
        fio_read = False
        fio_write = False
        result = False
        lines = output_iostat.split("\n")

        # Remove the initial iostat values
        lines_clean = lines[8:]

        iostat_sum = [0, 0, 0, 0, 0]
        for line in lines_clean:
            match_nvme = re.search(r'{}'.format(device), line)
            if match_nvme:
                match_numbers = re.findall(r'(?<= )[\d.]+', line)
                if len(match_numbers) == 5:
                    numbers = map(float, match_numbers)
                    iostat_sum = [sum(x) for x in zip(numbers, iostat_sum)]

        # read
        fun_test.log("IOstat sum: {}".format(iostat_sum))
        if iostat_sum[1] >= 0:
            fio_read = True
        # fun_test.test_assert(fio_read, "{} reads are resumed".format(host_name))

        # write
        if iostat_sum[2] >= 0:
            fio_write = True
        # fun_test.test_assert(fio_write, "{} writes are resumed".format(host_name))

        if fio_read or fio_write:
            result = True
        fun_test.test_assert(result, "Host: {}  IO running".format(host_name))

    def check_come_up_time(self, expected_minutes):
        initial = self.come_handle.command("uptime")
        output = self.come_handle.command("uptime")
        up_time = re.search(r'(\d+) min', output)
        up_time_less_than_5 = False
        if up_time:
            up_time_min = int(up_time.group(1))
            if up_time_min <= expected_minutes:
                up_time_less_than_5 = True
        fun_test.test_assert(up_time_less_than_5, "COMe 'up-time' less than 5 min")

    def check_expected_dockers_up(self):
        fun_test.log("Check if all the Dockers are up")
        docker_count = 0
        max_time = 100
        timer = FunTimer(max_time)
        while not timer.is_expired():
            docker_count = self.get_docker_count()
            if docker_count == self.expected_dockers:
                break
            else:
                fun_test.sleep("{} docker to be up".format(self.expected_dockers), seconds=5)
        fun_test.test_assert_expected(expected=self.expected_dockers, actual=docker_count, message="Docker's up")

    def check_portal_up(self):
        portal_up = False
        max_time = 300
        timer = FunTimer(max_time)
        while not timer.is_expired():
            try:
                status = urllib.urlopen("http://{}".format(self.fs['come']['mgmt_ip'])).getcode()
                fun_test.log("Return status: {}".format(status))
                if status == 200:
                    portal_up = True
                    break
                fun_test.sleep("Sleeping before next iteration")
            except Exception as ex:
                fun_test.log(ex)
        fun_test.test_assert(portal_up, "Portal is up")

    def verify_and_get_required_hosts_list(self, num_hosts):
        available_hosts_list = []
        try:
            self.topology_helper = TopologyHelper()
            self.topology_helper.set_dut_parameters(dut_index="6")
            available_hosts_list = OrderedDict(self.topology_helper.get_available_hosts())
            fun_test.log("Available hosts list: " + str(available_hosts_list))
            available_dut_indexes = self.topology_helper.get_available_duts().keys()
            fun_test.log("Available duts list: " + str(available_dut_indexes))
            if available_hosts_list:
                pass
            else:
                self.fs_hosts_map = utils.parse_file_to_json(SCRIPTS_DIR + "/storage/apple_rev2_fs_hosts_mapping.json")
                available_hosts_list = self.fs_hosts_map[self.testbed_type]["host_info"]
        except Exception as ex:
            fun_test.critical(ex)
        required_hosts_available = True if (len(available_hosts_list) >= num_hosts) else False
        fun_test.log("Expected hosts: {}, Available hosts: {}".format(num_hosts, len(available_hosts_list)))
        fun_test.test_assert(required_hosts_available, "Required hosts available")
        required_hosts_list = available_hosts_list[:num_hosts]
        return required_hosts_list

    def get_pool_id(self):
        response = self.sc_api.get_pools()
        fun_test.log("pools log: {}".format(response))
        pool_id = str(response['data'].keys()[0])
        fun_test.log("pool_id: {}".format(pool_id))
        return pool_id

    def create_vol(self, number_of_vol):
        volume_uuid_details = {}
        # If there is a need to create the volumes with different params can modify the code easily
        volume_creation_detail = self.volume_creation_details[0]
        for index in range(number_of_vol):
            volume_creation_detail["name"] = "{}{}".format(self.VOL_NAME, index + 1)
            response = self.sc_api.create_stripe_volume(pool_uuid=self.pool_uuid,
                                                        **volume_creation_detail)

            if response["status"]:
                message = response['message']
                volume_create_successful = True if message == 'volume create successful' else False
                fun_test.test_assert(volume_create_successful,
                                     "Create {} volume".format(volume_creation_detail["name"]))
            else:
                fun_test.test_assert(response["status"],
                                     "Create {} volume".format(volume_creation_detail["name"]))
            # Todo: get he api call for getting the existing volume details
            if "already exists" in response["error_message"]:
                pass
            vol_uuid = str(response['data']['uuid'])
            fun_test.log("volume creation log: {}".format(response))
            fun_test.log("volume creation status: {}".format(message))
            fun_test.log("vol UUID: {}".format(vol_uuid))
            volume_uuid_details[volume_creation_detail["name"]] = vol_uuid
        return volume_uuid_details

    def attach_volumes_to_host(self, required_hosts_list):
        self.host_details = {}
        # uuid = volume_uuid_details[vol_name]
        for index, host_name in enumerate(required_hosts_list):
            vol_name = self.VOL_NAME + str(index + 1)
            if vol_name in self.volume_uuid_details:
                pass
            else:
                if index == 0:
                    fun_test.critical("No volumes are created")
                vol_name = self.VOL_NAME + "1"
            host_interface_ip = self.hosts_asset[host_name]["test_interface_info"]["0"]["ip"].split("/")[0]
            response = self.sc_api.volume_attach_remote(vol_uuid=self.volume_uuid_details[vol_name],
                                                        remote_ip=host_interface_ip,
                                                        transport=self.transport_type.upper())

            fun_test.log("Volume attach response: {}".format(response))
            message = response["message"]
            attach_status = True if message == "Attach Success" else False
            fun_test.test_assert(attach_status, "Attach host: {} to volume: {}".format(host_name, vol_name))
            self.host_details[host_name] = {}
            self.host_details[host_name]["data"] = response["data"]
            self.host_details[host_name]["volume_name"] = vol_name
            self.host_details[host_name]["volume_uuid"] = self.volume_uuid_details[vol_name]

    def get_host_handles(self):
        for host_name in self.host_details:
            host_handle = self.get_host_handle(host_name)
            self.host_details[host_name]["handle"] = host_handle

    def get_host_handle(self, host_name):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        return host_handle

    def start_fio_and_verify(self, fio_params, host_names_list, cd="", toggle_read=True):
        thread_details = {}
        for host_name in host_names_list:
            thread_details[host_name] = {}
            run_time = fio_params.get("runtime", 60)
            if "read" in fio_params["rw"] and toggle_read:
                fio_params["rw"] = "randread" if fio_params["rw"] == "read" else "read"
            thread_details[host_name]["check"] = fun_test.execute_thread_after(func=self.check_traffic,
                                                                               time_in_seconds=5,
                                                                               fio_run_time=run_time,
                                                                               host_name=host_name)
            thread_details[host_name]["fio"] = fun_test.execute_thread_after(func=self.start_fio,
                                                                             time_in_seconds=7,
                                                                             fio_params=fio_params,
                                                                             host_name=host_name,
                                                                             run_time=run_time,
                                                                             cd=cd)

        for host_name in host_names_list:
            fun_test.join_thread(thread_details[host_name]["fio"])
            fun_test.join_thread(thread_details[host_name]["check"])

    def start_fio(self, host_name, fio_params, run_time, cd):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        if cd:
            host_handle.enter_sudo()
            host_handle.command("cd {}".format(cd))
        host_handle.pcie_fio(timeout=run_time+20,
                             filename=self.host_details[host_name]["nvme"],
                             **fio_params)
        host_handle.disconnect()

    def verify_nvme_connect(self):
        for host_name, host_info in self.host_details.iteritems():
            output_lsblk =  host_info["handle"].sudo_command("nvme list")
            lines = output_lsblk.split("\n")
            for line in lines:
                match_nvme_list = re.search(r'(?P<nvme_device>/dev/nvme\w+n\w+)', line)
                if match_nvme_list:
                    result = True
                    nvme_device = match_nvme_list.group("nvme_device")
            host_info["nvme"] = nvme_device
            fun_test.test_assert(result, "Host: {} nvme: {} verified NVME connect".format(host_name, nvme_device))

    def disconnect_the_hosts(self, strict=True):
        for host_name, host_info in self.host_details.iteritems():
            output = host_info["handle"].sudo_command("nvme disconnect -n {nqn}".format(nqn=host_info["data"]["subsys_nqn"]))
            strict_key = " 1" if strict else ""
            disconnected = True if "disconnected{}".format(strict_key) in output else False
            fun_test.test_assert(disconnected,
                                 "Host: {} disconnected from {}".format(host_name, host_info["data"]["ip"]))

    def delete_volumes(self):
        max_retries = 3
        for vol_name, vol_uuid in self.volume_uuid_details.iteritems():
            deleted = False
            for i in range(max_retries):
                response = self.sc_api.delete_volume(vol_uuid)
                fun_test.log("Volume delte response: {}".format(response))
                message = response["message"]
                deleted = True if message == "volume deletion successful" else False
                if deleted:
                    break
            fun_test.test_assert(deleted, "Delete volume :{} ".format(vol_name))

    def verify_volume_attach_detach(self, response, action="attach"):
        result = True
        if not response["status"]:
            result = False
        if result and (not "Success" in response["message"]):
            result = False
        fun_test.test_assert(result, "{} Volume {}ed successfully".format(self.volume_creation_details["name"], action))
        return result

    def intialize_the_hosts(self):
        for host_name, host_info in self.host_details.iteritems():
            module = "nvme"
            host_info["handle"].modprobe(module)
            module = "nvme_tcp"
            host_info["handle"].modprobe(module)

    def wipe_out_cassandra_es_database(self):
        self.come_handle.command("cd /var/opt/fungible")
        self.come_handle.sudo_command("rm -r elasticsearch")
        self.come_handle.sudo_command("rm -r cassandra")
        fun_test.test_assert(True, "Cleaned database")

    def restart_fs1600(self):
        self.come_handle.enter_sudo()
        self.come_handle.command("cd /opt/fungible/etc")
        self.come_handle.command("bash ResetFs1600.sh")

    def destoy_host_handles(self):
        for host_name in self.host_details:
            self.host_details[host_name]["handle"].destroy()

    def cleanup(self):
        if self.num_hosts:
            self.delete_volumes()


class DliPower:

    def __init__(self, hostname, userid="admin", password="Precious1*"):
        self.switch = dlipower.PowerSwitch(hostname=hostname, userid=userid, password=password)

    def outlet_on(self, outlet):
        # Reason for implementing this is to verify that the outlet is for sure turned on/off
        # >> switch.off(3) >> False
        # with this package False = Success. https://pypi.org/project/dlipower/0.2.33/
        result = True
        status = self.switch_status(outlet)
        if not status == "ON":
            self.switch.on(outlet)
            fun_test.sleep("After powering on")
            status = self.switch_status(outlet)
            if status == "ON":
                result = True
            else:
                result = False
        return result

    def outlet_off(self, outlet):
        result = True
        status = self.switch_status(outlet)
        if not status == "OFF":
            self.switch.off(outlet)
            status = self.switch_status(outlet)
            if status == "OFF":
                result = True
            else:
                result = False
        return result

    def switch_status(self, outlet):
        result = self.switch.status(outlet)
        return result

    def cycle(self, outlet):
        result = self.switch.cycle(outlet)
        return result

    def get_outlet_name(self, outlet):
        name = self.switch.get_outlet_name(outlet)
        return name


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
