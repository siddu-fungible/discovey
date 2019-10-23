from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.apc_pdu import ApcPdu
import re
import urllib
from lib.fun.fs import ComE, Bmc, Fpga
from lib.system import utils
from lib.host.linux import Linux
from collections import OrderedDict


class ApcPduScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

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
        fun_test.log(json.dumps(self.fs, indent=4))

        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict.iteritems():
            setattr(self, k, v)

        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)

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
            if "hosts" in job_inputs:
                self.hosts = job_inputs["hosts"]
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

            self.apc_pdu_reboot()
            self.come_handle.destroy()

            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])

            fun_test.log("Checking if BMC is UP")
            bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(bmc_up, "BMC is UP")

            fun_test.log("Checking if COMe is UP")
            come_up = self.come_handle.ensure_host_is_up(max_wait_time=600)
            fun_test.test_assert(come_up, "COMe is UP")

            self.check_come_up_time(expected_minutes=5)

            if self.check_docker:
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
                except Exception as ex:
                    fun_test.log(ex)

            fun_test.test_assert(portal_up, "Portal is up")

            # Check if lspci devices are detected
            fun_test.log("Check if F1_0 is detected")
            self.check_pci_dev(f1=0)

            fun_test.log("Check if F1_1 is detected")
            self.check_pci_dev(f1=1, fs_name=self.fs_name)

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

            # Todo: remove for loop in the helper script (previously had codded to work parallelly with multiple host,
            #  now we have to do it serially, so no need of for loops in helper function)
            if self.hosts:
                fun_test.sleep("Hosts to be up", seconds=self.after_runsc_up_host_connect_interval)
                hosts_list_with_handle = self.get_hosts_handle()
                for host_name, host in hosts_list_with_handle.iteritems():
                    single_host = {host_name: host}
                    self.connect_the_host(single_host)
                    host["nvme"] = self.get_nvme(single_host)
                    # Start traffic
                    self.run_traffic_bg(single_host)
                    # Check if traffic is running
                    self.check_traffic(single_host)
                    # Disconnect volume
                    self.disconnect_vol(single_host)
                    self.destroy_hosts_handle(single_host)

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

            fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=20)

            fun_test.log("Checking if COMe is down")
            come_down = not (self.come_handle.ensure_host_is_up(max_wait_time=10))
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

    def check_pci_dev(self, f1=0, fs_name=None):
        result = True
        bdf = '04:00.'
        if f1 == 1:
            bdf = '06:00.'
            if fs_name in ["fs-101", "fs-102", "fs-104"]:
                bdf = '05:00.'
        lspci_output = self.come_handle.command(command="lspci -d 1dad: | grep {}".format(bdf))
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

    def connect_the_host(self, hosts_list, retry=3):
        result = False
        for host_name, host in hosts_list.iteritems():
            # Try connecting nvme 3 times with an interval of 10 seconds each try, try 5 times
            for iter in range(retry):
                fun_test.log("Trying to connect to nvme, Iteration no: {} out of {}".format(iter + 1, retry))
                result = host["handle"].nvme_connect(target_ip=self.target_ip,
                                                     nvme_subsystem=host["nqn"],
                                                     nvme_io_queues=16,
                                                     retries=5,
                                                     timeout=100)
                if result:
                    break
                fun_test.sleep("before next iteration", seconds=10)

            fun_test.test_assert(result, "{} {} connected to {}".format(host_name, host["nqn"], self.target_ip))

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

    @staticmethod
    def run_traffic_bg(hosts_list):
        for host_name, host in hosts_list.iteritems():
            # result = host_handle.nvme_connect(target_ip=target_ip, nvme_subsystem=nqn)
            # fun_test.test_assert(result, "{} connected to {}".format(nqn, target_ip))
            # Run this in background if needed
            # fio_out = host_handle.pcie_fio(filename=filename, numjobs=4, iodepth=4, rw="randrw", direct=1,
            #                                ioengine="libaio", bs="4k", size="512g", name="fio_randrw", runtime=120,
            #                                do_verify=1, verify="md5", verify_fatal=1, timeout=300)
            host["handle"].enter_sudo()
            host["handle"].start_bg_process("fio --group_reporting --output-format=json --filename={filename} "
                                            "--time_based --rw=randrw --name=fio --iodepth=32 --verify=md5 --numjobs=1 "
                                            "--direct=1 --do_verify=1 --bs=4k --ioengine=libaio --runtime=120 "
                                            "--verify_fatal=1 --size=512g --output=/tmp/fio_power_cycler.txt".format(
                filename=host["nvme"]))
            # fun_test.test_assert(True, "{} fio started".format(host_name))
            host["handle"].exit_sudo()
            # if not fio_out:
            #     result = True
        return

    def check_traffic(self, hosts_list):
        for host_name, host in hosts_list.iteritems():
            device = host["nvme"]
            output_iostat = host["handle"].iostat(device=device, interval=10, count=13, background=False)
            device_name = device.replace("/dev/", '')
            self.ensure_io_running(device_name, output_iostat, host_name)
            fun_test.log(host["handle"].command("cat /tmp/fio_power_cycler.txt"))

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
        fun_test.test_assert(result, "{} IO is running".format(host_name))

    def disconnect_vol(self, hosts_list):
        for host_name, host in hosts_list.iteritems():
            result = False
            output = host["handle"].sudo_command("nvme disconnect -n {nqn}".format(nqn=host["nqn"]))
            if "disconnected" in output:
                result = True
            fun_test.test_assert(result, "Host {} disconnected from {}".format(host_name, self.target_ip))

    @staticmethod
    def destroy_hosts_handle(hosts_list):
        for host_name, host in hosts_list.iteritems():
            host["handle"].destroy()

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

    def cleanup(self):
        pass


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ApcPduTestcase())
    obj.run()
