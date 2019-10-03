from lib.system.fun_test import *
from collections import OrderedDict
import re
from lib.host.linux import Linux
import wrapper
HOSTS_ASSET = ASSET_DIR + "/hosts.json"
hosts = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)


def connect_the_host(hosts_list, target_ip):
    for host_name, host in hosts_list.iteritems():
        result = host["handle"].nvme_connect(target_ip=target_ip, nvme_subsystem=host["nqn"], nvme_io_queues=16)
        fun_test.test_assert(result, "{} {} connected to {}".format(host_name, host["nqn"], target_ip))
        host["handle"].sudo_command("nvme list")
        # output_lsblk = host_handle.lsblk()
        # for key in output_lsblk:
        #     if "nvme" in key:
        #         result = True
        #         break


        # fun_test.test_assert(result, "{} host is connected".format(host_name))


def add_hosts_handle(hosts_list):
    result = {}
    for host_name, nqn in hosts_list.iteritems():
        host_handle = get_host_handle(host_name)
        result[host_name] = {"nqn": nqn,
                             "handle": host_handle}
    return result


def destroy_hosts_handle(hosts_list):
    for host_name, host in hosts_list.iteritems():
        host["handle"].destroy()


def run_traffic_bg(hosts_list):
    for host_name, host in hosts_list.iteritems():
        # result = host_handle.nvme_connect(target_ip=target_ip, nvme_subsystem=nqn)
        # fun_test.test_assert(result, "{} connected to {}".format(nqn, target_ip))
        # Run this in background if needed
        # fio_out = host_handle.pcie_fio(filename=filename, numjobs=4, iodepth=4, rw="randrw", direct=1,
        #                                ioengine="libaio", bs="4k", size="512g", name="fio_randrw", runtime=120,
        #                                do_verify=1, verify="md5", verify_fatal=1, timeout=300)
        host["handle"].enter_sudo()
        host["handle"].start_bg_process("fio --group_reporting --output-format=json --filename=/dev/nvme0n1 "
                                        "--time_based --rw=randrw --name=fio --iodepth=32 --verify=md5 --numjobs=1 "
                                        "--direct=1 --do_verify=1 --bs=4k --ioengine=libaio --runtime=120 --verify_fatal=1 --size=512g")
        fun_test.test_assert(True, "{} fio started".format(host_name))
        host["handle"].exit_sudo()
        # if not fio_out:
        #     result = True
    return


def check_traffic(hosts_list):
    for host_name, host in hosts_list.iteritems():
        device = "/dev/nvme0n1"
        output_iostat = host["handle"].iostat(device=device, interval=10, count=13, background=False)
        device_name = "nvme0n1"
        wrapper.ensure_io_running(device_name, output_iostat, host_name)


def disconnect_vol(hosts_list, target_ip):
    for host_name, host in hosts_list.iteritems():
        # result = False
        result = host["handle"].sudo_command("nvme disconnect -d /dev/nvme0n1")
        result = host["handle"].sudo_command("nvme disconnect -d /dev/nvme1n1")
        # nvme_list_raw = host["handle"].sudo_command("nvme list -o json")
        # try:
        #     nvme_list_dict = json.loads(nvme_list_raw)
        # except:
        #     nvme_list_raw = nvme_list_raw + "}"
        #     nvme_list_dict = json.loads(nvme_list_raw, strict=False)
        #
        # nvme_device_list = []
        # for device in nvme_list_dict["Devices"]:
        #     if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"]:
        #         nvme_device_list.append(device["DevicePath"])
        #     elif "Unknown Device" in device["ProductName"]:
        #         if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
        #             nvme_device_list.append(device["DevicePath"])
        # for device in nvme_device_list:
        #     result = host["handle"].sudo_command("nvme disconnect -d {}".format(device))
        #     fun_test.test_assert(result, "Host {} disconnected from {}".format(host_name, target_ip))


def check_docker(come_handle, expected=3):
    output = come_handle.command("docker ps -a")
    num_docker = wrapper.docker_get_num_dockers(output)
    fun_test.test_assert_expected(expected=expected, actual=num_docker, message="Docker's up")


def check_pci_dev(come_handle, f1=0):
    result = True
    bdf = '04:00.'
    if f1 == 1:
        bdf = '06:00.'
    lspci_output = come_handle.command(command="lspci -d 1dad: | grep {}".format(bdf))
    sections = ['Ethernet controller', 'Non-Volatile', 'Unassigned class', 'encryption device']
    for section in sections:
        if section not in lspci_output:
            result = False
            fun_test.critical("Under LSPCI {} not found".format(section))
    return result


def check_ssd(come_handle, expected_ssds_up=6, f1=0):
    result = False
    if expected_ssds_up == 0:
        return True
    dpcsh_data = get_dpcsh_data_for_cmds(come_handle, "peek storage/devices/nvme/ssds", f1)
    if dpcsh_data:
        validate = validate_ssd_status(dpcsh_data, expected_ssds_up, f1)
        if validate:
            result = True
    fun_test.test_assert(result, "F1_{}: SSD's ONLINE".format(f1))
    return result


def check_nu_ports(come_handle,
                   iteration,
                   expected_ports_up=None,
                   f1=0):
    result = False
    dpcsh_output = get_dpcsh_data_for_cmds(come_handle, "port linkstatus", f1)
    if dpcsh_output:
        ports_up = validate_link_status_out(dpcsh_output,
                                            f1=f1,
                                            iteration=iteration,
                                            expected_port_up=expected_ports_up)
        if ports_up:
            result = True
    return result


def check_come_up_time(come_handle, expected_seconds=5):
    initial = come_handle.command("uptime")
    output = come_handle.command("uptime")
    up_time = re.search(r'(\d+) min', output)
    up_time_less_than_5 = False
    if up_time:
        up_time_min = int(up_time.group(1))
        if up_time_min <= expected_seconds:
            up_time_less_than_5 = True
    fun_test.test_assert(up_time_less_than_5, "COMe 'up-time' less than 5 min")


# Validation


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


def validate_link_status_out(link_status_out,
                             expected_port_up,
                             f1=0,
                             iteration=1):
    result = True
    link_status = parse_link_status_out(link_status_out, f1=f1, iteration=iteration)
    if link_status:
        if not expected_port_up:
            speed = link_status['lport-0']['speed']
            if speed == "10G":
                expected_port_up = {'NU': range(24), 'HNU': []}
            elif speed == "100G":
                expected_port_up = {'NU': [0, 4, 8, 12], 'HNU': []}

        name_xcvr_dict = get_name_xcvr(link_status)
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


def get_name_xcvr(parsed_output):
    result = {}
    if parsed_output:
        for each_port, value in parsed_output.iteritems():
            result[value['name']] = value['xcvr']
    return result

# Parsing


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


# Dpcsh no cli: returns the dpcsh output data for the given command


def get_dpcsh_data_for_cmds(come_handle, cmd, f1=0):
    result = False
    try:
        come_handle.enter_sudo()
        come_handle.command("cd /opt/fungible/FunSDK/bin/Linux/dpcsh")
        run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
        output = come_handle.command(run_cmd)
        result = parse_dpcsh_output(output)
        come_handle.exit_sudo()
    except:
        fun_test.log("Unable to get the DPCSH data for command: {}".format(cmd))
    return result

# Common functions


def get_host_handle(host_name):
    host_info = hosts[host_name]
    host_handle = Linux(host_ip=host_info['host_ip'],
                        ssh_username=host_info['ssh_username'],
                        ssh_password=host_info['ssh_password'])
    return host_handle
