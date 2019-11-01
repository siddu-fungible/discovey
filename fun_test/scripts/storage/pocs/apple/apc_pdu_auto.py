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
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)
        fun_test.log(json.dumps(self.fs, indent=4))

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
            if "docker_verify_interval" in job_inputs:
                self.docker_verify_interval = job_inputs["docker_verify_interval"]
            if "after_runsc_up_host_connect_interval" in job_inputs:
                self.after_runsc_up_host_connect_interval = job_inputs["after_runsc_up_host_connect_interval"]
            if "check_portal" in job_inputs:
                self.check_portal = job_inputs["check_portal"]
            if "apc_pdu_reboot_machine" in job_inputs:
                self.apc_pdu_reboot_machine = job_inputs["apc_pdu_reboot_machine"]

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
            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])
            self.bmc_handle.set_prompt_terminator(r'# $')

            fun_test.add_checkpoint(checkpoint="ITERATION : {} out of {}".format(pc_no + 1, self.iterations))

            if self.apc_pdu_reboot_machine:
                self.apc_pdu_reboot()
            self.come_handle.destroy()
            self.bmc_handle.destroy()

            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])
            self.bmc_handle.set_prompt_terminator(r'# $')

            fun_test.log("Checking if COMe is UP")
            come_up = self.come_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(come_up, "COMe is UP")

            fun_test.log("Checking if BMC is UP")
            bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(bmc_up, "BMC is UP")

            if self.apc_pdu_reboot_machine:
                self.check_come_up_time(expected_minutes=5)

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
                self.check_nu_ports(f1=0, expected_ports_up=expected_ports_up_f1_0)

                expected_ports_up_f1_1 = {'NU': self.expected_nu_ports_f1_1,
                                          'HNU': self.expected_hnu_ports_f1_1}
                fun_test.log("Checking if NU and HNU port's are active on F1_1")
                self.check_nu_ports(f1=1, expected_ports_up=expected_ports_up_f1_1)

            if self.num_hosts:
                if pc_no == 0:
                    required_hosts_list = self.verify_and_get_required_hosts_list()
                    self.volume_uuid_details = self.create_vol_using_api()
                    self.attach_volumes_to_host(self.volume_uuid_details, required_hosts_list)
                    self.get_host_handles()
                    self.intialize_the_hosts()
                self.get_host_handles()
                self.connect_the_host_to_volumes()
                self.verify_nvme_connect()
                self.start_traffic_and_verify()
                self.disconnect_the_hosts()
                self.destoy_host_handles()

            self.come_handle.destroy()
            self.bmc_handle.destroy()
            self.come_handle.destroy()
            self.bmc_handle.destroy()

            fun_test.sleep("before next iteration", seconds=self.end_sleep)

    def apc_pdu_reboot(self):
        '''
        1. check if COMe is up, than power off.
        2. check COMe now, if its down tha power on
        :param come_handle:
        :return:
        '''
        try:
            fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))

            fun_test.log("Checking if COMe is UP")
            come_up = self.come_handle.ensure_host_is_up()
            fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                    self.to_str(come_up), True, come_up)
            self.come_handle.destroy()

            apc_pdu = ApcPdu(host_ip=self.apc_info['host_ip'], username=self.apc_info['username'],
                             password=self.apc_info['password'])
            fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

            apc_outlet_off_msg = apc_pdu.outlet_off(self.outlet_no)
            fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
            outlet_off = self.match_success(apc_outlet_off_msg)
            fun_test.test_assert(outlet_off, "Power down FS")

            fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

            fun_test.log("Checking if COMe is down")
            come_down = not (self.come_handle.ensure_host_is_up(max_wait_time=15))
            fun_test.test_assert(come_down, "COMe is Down")
            self.come_handle.destroy()

            apc_outlet_on_msg = apc_pdu.outlet_on(self.outlet_no)
            fun_test.log("APC PDU outlet on message {}".format(apc_outlet_on_msg))
            outlet_on = self.match_success(apc_outlet_on_msg)
            fun_test.test_assert(outlet_on, "Power on FS")

            apc_pdu.disconnect()
        except Exception as ex:
            fun_test.critical(ex)

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

    def check_pci_dev(self, f1=0):
        result = True
        bdf = '04:00.'
        if f1 == 1:
            bdf = '06:00.'
            if self.fs_name in ["fs-101", "fs-102", "fs-104"]:
                bdf = '05:00.'
        lspci_output = self.come_handle.command("lspci -d 1dad: | grep {}".format(bdf), timeout=120)
        sections = ['Ethernet controller', 'Non-Volatile', 'Unassigned class', 'encryption device']
        for section in sections:
            if section not in lspci_output:
                result = False
                fun_test.critical("Under LSPCI {} not found".format(section))
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

    def get_dpcsh_data_for_cmds(self, cmd, f1=0):
        result = False
        try:
            self.come_handle.enter_sudo()
            self.come_handle.command("cd /opt/fungible/FunSDK/bin/Linux/dpcsh")
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
        link_status = self.parse_link_status_out(link_status_out, f1=f1, iteration=self.pc_no)
        if link_status:
            if not expected_port_up:
                speed = link_status['lport-0']['speed']
                if speed == "10G":
                    expected_port_up = {'NU': range(24), 'HNU': []}
                elif speed == "100G":
                    expected_port_up = {'NU': [0, 4, 8, 12], 'HNU': []}

            name_xcvr_dict = self.get_name_xcvr(link_status)
            for field in ['NU', 'HNU']:
                if expected_port_up[field]:
                    for port in expected_port_up[field]:
                        nu_port_name = '{}-FPG-{}'.format(field, port)
                        if not (nu_port_name in name_xcvr_dict):
                            return False
                        if name_xcvr_dict[nu_port_name] == 'ABSENT':
                            return False

        else:
            result = False
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
                                             r'admin:(?P<admin>[\w ]+)\s+SW:\s+(?P<sw>\d+)\s+HW:\s+(?P<hw>\d+)\s+'
                                             r'LPBK:\s+(?P<lpbk>\d+)\s+FEC:\s+(?P<fec>\d+)', value)
                    if match_fields:
                        one_data_set = {}
                        one_data_set['name'] = match_fields.group('name').replace(' ', '')
                        one_data_set['xcvr'] = match_fields.group('xcvr')
                        one_data_set['speed'] = match_fields.group('speed')
                        one_data_set['admin'] = match_fields.group('admin')
                        one_data_set['sw'] = match_fields.group('sw')
                        one_data_set['hw'] = match_fields.group('hw')
                        one_data_set['lpbk'] = match_fields.group('lpbk')
                        one_data_set['fec'] = match_fields.group('fec')
                        table_data_rows.append([one_data_set['name'], one_data_set['xcvr'], one_data_set['speed'],
                                                one_data_set['admin'], one_data_set['sw'], one_data_set['hw'],
                                                one_data_set['lpbk'], one_data_set['fec']])
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
        output = self.come_handle.command("docker ps -a")
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
                nqn = host_info["data"]["nqn"]
                target_ip = host_info["data"]["ip"]
                result = host_info["handle"].nvme_connect(target_ip=target_ip,
                                                          nvme_subsystem=nqn,
                                                          nvme_io_queues=16,
                                                          retries=5,
                                                          timeout=100)
                if result:
                    break
                fun_test.sleep("Before next iteration", seconds=10)

            fun_test.test_assert(result, "Host: {} nqn: {} connected to DataplaneIP: {}".format(host_name, nqn, target_ip))

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

    def check_traffic(self, host_name):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        device = self.host_details[host_name]["nvme"]
        device_name = device.replace("/dev/", '')
        count = self.fio["runtime"] / 10
        output_iostat = host_handle.iostat(device=device, interval=10, count=count, background=False)
        self.ensure_io_running(device_name, output_iostat, host_name)
        fun_test.log(host_handle.command("cat /tmp/{}_fio.txt".format(host_name)))

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
        if iostat_sum[1] > 20:
            fio_read = True
        # fun_test.test_assert(fio_read, "{} reads are resumed".format(host_name))

        # write
        if iostat_sum[2] > 20:
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

    def verify_and_get_required_hosts_list(self):
        available_hosts_list = []
        try:
            self.fs_hosts_map = utils.parse_file_to_json(SCRIPTS_DIR + "/storage/apple_rev2_fs_hosts_mapping.json")
            available_hosts_list = self.fs_hosts_map[self.fs_name]["host_info"]
        except Exception as ex:
            fun_test.critical(ex)
        required_hosts_available = True if (len(available_hosts_list) >= self.num_hosts) else False
        fun_test.log("Expected hosts: {}, Available hosts: {}".format(self.num_hosts, len(available_hosts_list)))
        fun_test.test_assert(required_hosts_available, "Required hosts available")
        required_hosts_list = available_hosts_list[:self.num_hosts]
        return required_hosts_list

    def create_vol_using_api(self):
        self.portal_username = 'admin'
        self.portal_password = 'password'
        self.apiprotocol = "http"
        self.api_server_port = 50220

        self.http_basic_auth = requests.auth.HTTPBasicAuth(self.portal_username, self.portal_password)
        self.pool_id = self.get_pool_id()
        volume_uuid_details = self.create_vol()
        return volume_uuid_details

    def get_pool_id(self):
        data = []
        pool_url = '{}://{}:{}/FunCC/v1/storage/pools'.format(self.apiprotocol, self.fs['come']['mgmt_ip'], self.api_server_port)
        response = requests.get(pool_url, auth=self.http_basic_auth, json=data, verify=False)
        fun_test.log("pools log: {}".format(response.json()))
        pool_id = str(response.json()['data'].keys()[0])
        fun_test.log("pool_id: {}".format(pool_id))
        return pool_id

    def topology_request(self):
        data = []
        topo_url = '{}://{}:{}/FunCC/v1/topology'.format(self.apiprotocol, self.fs['come']['mgmt_ip'], self.api_server_port)
        response = requests.get(self.topo_url, auth=self.http_basic_auth, json=data, verify=False)
        fun_test.log("topology log: {}".format(response.json()))

    def create_vol(self):
        volume_uuid_details = {}
        # If there is a need to create the volumes with different params can modify the code easily
        volume_creation_detail = self.volume_creation_details[0]
        for index in range(self.num_hosts):
            volume_creation_detail["name"] = "Stripe{}".format(index+1)
            volcreate_url = "{}://{}:{}/FunCC/v1/storage/pools/{}/volumes".format(self.apiprotocol,
                                                                                  self.fs['come']['mgmt_ip'],
                                                                                  self.api_server_port,
                                                                                  self.pool_id)
            data = {"name": volume_creation_detail["name"], "capacity": volume_creation_detail["capacity"],
                    "vol_type": volume_creation_detail["vol_type"],
                    "encrypt": volume_creation_detail["encrypt"], "allow_expansion": False,
                    "stripe_count": volume_creation_detail["stripe_count"],
                    "data_protection": {}, "compression_effort": volume_creation_detail["compression_effort"]}
            response = requests.post(volcreate_url, auth=self.http_basic_auth, json=data, verify=False)
            try:
                response_json = response.json()
            except Exception as ex:
                fun_test.log(ex)
                fun_test.test_assert(False,
                                     "Create {} volume".format(volume_creation_detail["name"]))
            message = response_json['message']
            volume_create_successful = True if message == 'volume create successful' else False
            fun_test.test_assert(volume_create_successful,
                                 "Create {} volume".format(volume_creation_detail["name"]))
            # Todo: get he api call for getting the existing volume details
            if "already exists" in response_json["error_message"]:
                pass
            vol_uuid = str(response_json['data']['uuid'])
            fun_test.log("volume creation log: {}".format(response.json()))
            fun_test.log("volume creation status: {}".format(message))
            fun_test.log("vol UUID: {}".format(vol_uuid))
            volume_uuid_details[volume_creation_detail["name"]] = vol_uuid
        return volume_uuid_details

    def attach_volumes_to_host(self, volume_uuid_details, required_hosts_list):
        self.host_details = {}
        # uuid = volume_uuid_details[vol_name]
        for vol_name, host_name in zip(volume_uuid_details, required_hosts_list):
            volattach_url = "{}://{}:{}/FunCC/v1/storage/volumes/{}/ports".format(self.apiprotocol,
                                                                                  self.fs['come']['mgmt_ip'],
                                                                                  self.api_server_port,
                                                                                  volume_uuid_details[vol_name])
            host_interface_ip = self.hosts_asset[host_name]["test_interface_info"]["0"]["ip"].split("/")[0]
            data = {"remote_ip": host_interface_ip, "transport": self.transport_type.upper()}
            response = requests.post(volattach_url, auth=self.http_basic_auth, json=data, verify=False)
            try:
                response_json = response.json()
            except Exception as ex:
                fun_test.critical(ex)
            fun_test.log("Volume attach response: {}".format(response_json))
            message = response_json["message"]
            attach_status = True if message == "Attach Success" else False
            fun_test.test_assert(attach_status, "Attach host: {} to volume: {}".format(host_name, vol_name))
            self.host_details[host_name] = {}
            self.host_details[host_name]["data"] = response_json["data"]
            self.host_details[host_name]["volume_name"] = vol_name

    def get_host_handles(self):
        for host_name in self.host_details:
            host_info = self.hosts_asset[host_name]
            host_handle = Linux(host_ip=host_info['host_ip'],
                                ssh_username=host_info['ssh_username'],
                                ssh_password=host_info['ssh_password'])
            self.host_details[host_name]["handle"] = host_handle


    def start_traffic_and_verify(self):
        thread_details = {}
        for host_name, host_info in self.host_details.iteritems():
            thread_details[host_name] = {}
            thread_details[host_name]["fio"] = fun_test.execute_thread_after(func=self.start_fio,
                                                                             time_in_seconds=5,
                                                                             host_name=host_name)
            thread_details[host_name]["check"] = fun_test.execute_thread_after(func=self.check_traffic,
                                                                               time_in_seconds=20,
                                                                               host_name=host_name)

        for host_name in self.host_details:
            fun_test.join_thread(thread_details[host_name]["fio"])
            fun_test.join_thread(thread_details[host_name]["check"])

    def start_fio(self, host_name):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])

        host_handle.pcie_fio(timeout=600,
                             filename=self.host_details[host_name]["nvme"],
                             **self.fio)


    def verify_nvme_connect(self):
        for host_name, host_info in self.host_details.iteritems():
            output_lsblk = host_info["handle"].sudo_command("nvme list")
            nsid = host_info["data"]["nsid"]
            lines = output_lsblk.split("\n")
            for line in lines:
                match_nvme_list = re.search(r'(?P<nvme_device>/dev/nvme\w+)\s+(?P<namespace>\d+)\s+(\d+)', line)
                if match_nvme_list:
                    namespace = int(match_nvme_list.group("namespace"))
                    if namespace == nsid:
                        host_info["nvme"] = match_nvme_list.group("nvme_device")
                        fun_test.log("Host: {} is connected by nvme device: {}".format(host_name, host_info["nvme"]))
                        break
            verify_nvme_connect = True if "nvme" in host_info else False
            fun_test.test_assert(verify_nvme_connect, "Host: {} nvme: {} verified NVME connect".format(host_name,
                                                                                                       host_info["nvme"]
                                                                                                       ))

    def disconnect_the_hosts(self):
        for host_name, host_info in self.host_details.iteritems():
            output = host_info["handle"].sudo_command("nvme disconnect -n {nqn}".format(nqn=host_info["data"]["nqn"]))
            disconnected = True if "disconnected" in output else False
            fun_test.test_assert(disconnected,
                                 "Host: {} disconnected from {}".format(host_name, host_info["data"]["ip"]))

    def delete_volumes(self):
        try:
            data = {}
            for vol_name, vol_uuid in self.volume_uuid_details.iteritems():
                delete_vol_url = "{}://{}:{}/FunCC/v1/storage/volumes/{}".format(self.apiprotocol,
                                                                                 self.fs['come']['mgmt_ip'],
                                                                                 self.api_server_port,
                                                                                 vol_uuid)
                response = requests.delete(delete_vol_url, auth=self.http_basic_auth, json=data, verify=False)
                response_json = response.json()
                fun_test.log("Volume delte response: {}".format(response_json))
                message = response_json["message"]
                deleted = True if message == "volume deletion successful" else False
                fun_test.test_assert(deleted, "Delete volume :{} ".format(vol_name))
        except Exception as ex:
            fun_test.log(ex)

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

    def restart_fs1600(self):
        self.come_handle.command("cd /opt/fungible/etc")
        self.come_handle.command("bash ResetFs1600.sh")

    def destoy_host_handles(self):
        for host_name in self.host_details:
            self.host_details[host_name]["handle"].destroy()

    def cleanup(self):
        if self.num_hosts:
            self.delete_volumes()
        # self.disconnect_the_hosts()

if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
