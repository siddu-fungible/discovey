from lib.system.fun_test import *
import re


def get_dpcsh_output(come_handle, cmd, f1=0):
    result = False
    try:
        come_handle.enter_sudo()
        come_handle.command("cd /scratch/FunSDK/bin/Linux")
        run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
        output = come_handle.command(run_cmd, timeout=10000)
        result = parse_dpcsh_output(output)
        come_handle.exit_sudo()
    except Exception as ex:
        fun_test.critical(ex)
    return result


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


def start_dpcsh_bg(come_handle, cmd, f1=0):
    result = False
    try:
        print("Command : {}".format(cmd))
        come_handle.enter_sudo()
        come_handle.command("cd /scratch/FunSDK/bin/Linux")
        run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
        pid = come_handle.start_bg_process(run_cmd)
        come_handle.exit_sudo()
        result = True
    except Exception as ex:
        fun_test.critical(ex)
    return result
