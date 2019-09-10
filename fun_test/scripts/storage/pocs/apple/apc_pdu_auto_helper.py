from lib.system.fun_test import *
from collections import OrderedDict
import re


def check_ssd(come_handle, expected_ssds_up=6, f1=0):
    result = False
    dpcsh_data = get_dpcsh_data_for_cmds(come_handle, "peek storage/devices/nvme/ssds", f1)
    if dpcsh_data:
        validate = validate_ssd_status(dpcsh_data, expected_ssds_up)
        if validate:
            result = True
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


# Validation


def validate_ssd_status(dpcsh_data, expected_ssd_count):
    result = True
    if dpcsh_data:
        ssds_count = len(dpcsh_data)
        if ssds_count >= expected_ssd_count:
            for each_ssd, value in dpcsh_data.iteritems():
                if "device state" in value:
                    if not (value["device state"] == "DEV_ONLINE"):
                        result = False
        else:
            result = False
            fun_test.add_checkpoint("Expected ssds count : {}", FunTest.FAILED, True, result)
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
        come_handle.command("cd /scratch/FunSDK/bin/Linux")
        run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
        output = come_handle.command(run_cmd)
        result = parse_dpcsh_output(output)
        come_handle.exit_sudo()
    except:
        fun_test.log("Unable to get the DPCSH data for command: {}".format(cmd))
    return result


if __name__ == "__main__":
    dpcsh_data = {
    "LINK STATUS": "LINK STATUS",
    "lport- 0": " NU-FPG- 0 xcvr:PRESENT  speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 1": " NU-FPG- 1 xcvr:PRESENT  speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 2": " NU-FPG- 2 xcvr:PRESENT  speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 3": " NU-FPG- 3 xcvr:PRESENT  speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 4": " NU-FPG- 4 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 5": " NU-FPG- 5 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 6": " NU-FPG- 6 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 7": " NU-FPG- 7 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 8": " NU-FPG- 8 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport- 9": " NU-FPG- 9 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-10": " NU-FPG-10 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-11": " NU-FPG-11 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-12": " NU-FPG-12 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-13": " NU-FPG-13 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-14": " NU-FPG-14 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-15": " NU-FPG-15 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-16": " NU-FPG-16 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-17": " NU-FPG-17 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-18": " NU-FPG-18 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-19": " NU-FPG-19 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-20": " NU-FPG-20 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-21": " NU-FPG-21 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-22": " NU-FPG-22 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-23": " NU-FPG-23 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-61": " NU-MPG- 0 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-64": "HNU-FPG- 0 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-65": "HNU-FPG- 1 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-66": "HNU-FPG- 2 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-67": "HNU-FPG- 3 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-68": "HNU-FPG- 4 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-69": "HNU-FPG- 5 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-70": "HNU-FPG- 6 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-71": "HNU-FPG- 7 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-72": "HNU-FPG- 8 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-73": "HNU-FPG- 9 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-74": "HNU-FPG-10 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-75": "HNU-FPG-11 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-76": "HNU-FPG-12 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-77": "HNU-FPG-13 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-78": "HNU-FPG-14 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0",
    "lport-79": "HNU-FPG-15 xcvr:ABSENT   speed:  10G admin:NOSHUT SW: 0 HW: 0 LPBK: 0 FEC: 0"}
    print validate_link_status_out(dpcsh_data, {"NU": [0,1,2,3], "HNU": []})