import re
from lib.fun.fs import ComE, Bmc
from asset.asset_manager import AssetManager
from lib.system.fun_test import *


FILENAME = "f1_power.sh"
REMOTE_PATH = "/tmp/" + FILENAME

# power_shell = fun_test.get_test_case_artifact_file_name(post_fix_name="power_shell_script_logs.txt")
# f_power_shell = open(power_shell, 'w+')
# power_output = fun_test.get_test_case_artifact_file_name(post_fix_name="power_output_logs.txt")
# f_power_output = open(power_output, 'w+')


def run_fs_power_script(bmc_handle):
    result = False
    output = bmc_handle.command("/mnt/sdmmc0p1/scripts/psu-power.sh", timeout=3000)
    result = parse_fs_power(output)
    fun_test.log("FS power: {}".format(result))
    # file_helper.add_data(f_power_shell, output, heading=heading)
    return output, result


def run_f1_power_script(bmc_handle):
    output = bmc_handle.command("sh /mnt/sdmmc0p1/scripts/f1_power.sh", timeout=3000)
    power_dict = parse_power_output(output)
    fun_test.log("F1 power: {}".format(power_dict))
    return output, power_dict


def parse_fs_power(output):
    fs_power = 0
    if output:
        lines = output.split('\n')
        for line in lines:
            match_power_out = re.search("PSU0\s+POUT\d\s+([\d.]+)", line)
            if match_power_out:
                fs_power += float(match_power_out.group(1))
    return fs_power


def parse_power_output(output):
    result = {}
    output = output.split('\n')
    result['F1_0'] = [0,0,0,0,0,0]
    result['F1_1'] = [0,0,0,0,0,0]
    result['FS'] = None

    for index, line in enumerate(output):
        match_pattern = re.search(r'F1_(?P<f1>[01])_(?P<name1>[\w]+).*', line)
        if match_pattern:
            value1 = float(re.search(r'[0-9.]+', output[index+1]).group())
            value2 = float(re.search(r'[0-9.]+', output[index+2]).group())

            f1 = match_pattern.group('f1')
            name = match_pattern.group('name1')

            if name == 'VDD0V8':
                result['F1_{}'.format(f1)][0] = value1 * 3
                result['F1_{}'.format(f1)][1] = value2 * 3
            elif name == 'VDD1V2':
                result['F1_{}'.format(f1)][2] = value1
                result['F1_{}'.format(f1)][3] = value2
            elif name == 'AVDD0V9':
                result['F1_{}'.format(f1)][4] = value1
                result['F1_{}'.format(f1)][5] = value2

    result['F1_0'] = round(sum(result['F1_0']), 4)
    result['F1_1'] = round(sum(result['F1_1']), 4)
    result['FS'] = round(result['F1_0'] + result['F1_1'], 2)
    return result


def format_the_power_result(fs_power, f1_power):
    data = ""
    data += "F1 0 power        : {}\n".format(f1_power['F1_0'])
    data += "F1 1 power        : {}\n".format(f1_power['F1_1'])
    data += "Total F1 power    : {}\n".format(f1_power['FS'])
    data += "FS   power        : {}\n".format(fs_power)
    return data


# Get the raw output for F1 and Fs power calculate and return the texts


def power_manager(bmc_handle):
    result = {}
    fs_raw, fs_cal = run_fs_power_script(bmc_handle)
    f1_raw, f1_cal = run_f1_power_script(bmc_handle)
    raw_output = fs_raw + "\n\n\n" + f1_raw
    result["fs_power"] = fs_cal
    result["f1_0_power"] = f1_cal['F1_0']
    result["f1_1_power"] = f1_cal['F1_1']
    result["total_f1_power"] = f1_cal['F1_0'] + f1_cal['F1_1']

    cal_output = format_the_power_result(fs_cal, f1_cal)
    # print (raw_output)
    # print (cal_output)
    return raw_output, cal_output, result


def die_temperature(bmc_handle):
    output = bmc_handle.command("ipmitool -I lanplus -H 10.1.21.0 -U admin -P admin sensor")
    return output


def new_power(bmc_handle):
    cmd = "/mnt/sdmmc0p1/scripts/new_power.sh"
    output = bmc_handle.command(cmd)
    return output


if __name__ == "__main__":
    fs = AssetManager().get_fs_spec("fs-65")
    bmc_handle = Bmc(host_ip=fs['bmc']['mgmt_ip'],
                     ssh_username=fs['bmc']['mgmt_ssh_username'],
                     ssh_password=fs['bmc']['mgmt_ssh_password'],
                     set_term_settings=True,
                     disable_uart_logger=False)
    bmc_handle.set_prompt_terminator(r'# $')
    # run_fs_power_script(bmc_handle)
    # run_f1_power_script(bmc_handle)
    power_manager(bmc_handle)
