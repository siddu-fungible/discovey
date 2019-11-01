import dpcsh_nocli
from lib.system.fun_test import *
from lib.host.linux import Linux

vm_0 = {
    "name": "elk",
    "host_ip":"10.1.20.52",
    "ssh_username": "localadmin",
    "ssh_password": "Precious1*",
    "WORKSPACE": "/home/localadmin/Integration",
    "PYTHONPATH": "/home/localadmin/Integration/fun_test",
    "SCRIPT_PATH": "/home/localadmin/Integration/fun_test/scripts/power_monitor"
}
vm_1 = {
    "name": "onkar_cloned",
    "host_ip": "10.1.23.228",
    "ssh_username": "localadmin",
    "ssh_password": "r00t.!@#",
    "WORKSPACE": "/home/localadmin/fungible_automation/Integration",
    "PYTHONPATH": "/home/localadmin/fungible_automation/Integration/fun_test",
    "SCRIPT_PATH": "/home/localadmin/fungible_automation/Integration/fun_test/scripts/power_monitor"
}
vm_info = None

def crypto(come_handle, vp_iters=500000, src='ddr', dst='ddr', f1=0, nvps=48):
    result = False
    try:
        json_data = {'src': src, 'dst': dst, 'vp_iters': vp_iters, 'cr_test_mute': True, "nvps": nvps}
        cmd = "async crypto_raw_speed %s" % json_data
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
        result = True
    except Exception as ex:
        fun_test.critical(ex)
    return result


def zip_deflate(come_handle, compress=True, nflows=7680, niterations=100, max_effort=0, f1=0, npcs=None):
    result = False
    try:
        json_data = {"niterations": niterations,
                     "nflows": nflows,
                     "max_effort": max_effort,
                     }
        if npcs:
            json_data['npcs'] = npcs
        cmd = "async deflate_perf_multi %s" % json_data
        # cmd = "async deflate_perf_multi"
        print (cmd)
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
        result = True
    except Exception as ex:
        fun_test.critical(ex)
    return result


def rcnvme(come_handle,
           all_ctrlrs='true',
           duration=60,
           qdepth=12,
           nthreads=12,
           test_type='read_only',
           hbm='true',
           prealloc='true',
           iosize=4096,
           random='true',
           f1=0):
    result = False
    try:
        json_data = '"all_ctrlrs" : {}, "qdepth": {}, "nthreads" : {},"test_type":{},' \
             '  "hbm" : {},  "prealloc":{}, "iosize":{}, "random": {}, "duration" : {}'.format(all_ctrlrs,
                                                                                               qdepth,
                                                                                               nthreads,
                                                                                               test_type,
                                                                                               hbm,
                                                                                               prealloc,
                                                                                               iosize,
                                                                                               random,
                                                                                               duration)

        cmd = 'async rcnvme_test{%s}' % json_data
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
        result = True
    except Exception as ex:
        fun_test.critical(ex)
    return result


def fio(come_handle, f1=0, num_jobs=8, run_time=80, iodepth=16):
    result = False
    try:
        cmd = "fio --group_reporting --output-format=json --ioengine=libaio --filename=/dev/nvme{f1}n1" \
              " --time_based --output-format=json --rw=randread --name=fio_ec_default --prio=0" \
              " --numjobs={num_jobs} --direct=1 --cpus_allowed=0-7 --bs=4k --runtime={run_time} --iodepth={iodepth}" \
              " --size=100%".format(f1=f1, num_jobs=num_jobs, run_time=run_time, iodepth=iodepth)
        come_handle.enter_sudo()
        come_handle.start_bg_process(cmd, output_file="/tmp/f1_{}_fio_nj{}_io{}_run{}_logs.txt"
                                     .format(f1, num_jobs, iodepth, run_time))
        come_handle.exit_sudo()
        result = True

    except Exception as ex:
        fun_test.critical(ex)
    return result

def le_firewall(run_time, new_image, just_kill=False):
    global vm_info
    if new_image:
        run_time += 400
    else:
        run_time += 200
    vm_info = {}

    for vm_number in range(2):
        vm = globals()["vm_{}".format(vm_number)]
        handle = Linux(host_ip=vm["host_ip"], ssh_username=vm["ssh_username"], ssh_password=vm["ssh_password"])
        vm_info[vm["name"]] = {}
        vm_info[vm["name"]]["handle"] = handle
        vm_info[vm["name"]].update(vm)

    if just_kill:
        for vm, vm_details in vm_info.iteritems():
            kill_le_firewall(vm_details)

        return
    for vm, vm_details in vm_info.iteritems():
        running = check_if_le_firewall_is_running(vm_details)
        if running and not new_image:
            kill_le_firewall(vm_details)
        if not running and new_image:
            tmp_run_time = 30
            cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":true}' ''' % tmp_run_time
            initiate_or_run_le_firewall(cmd, vm_details)
            running = check_if_le_firewall_is_running(vm_details)
            if running:
                fun_test.test_assert(running, "Le initiate started on the VM: {}".format(vm))
    if new_image:
        pid_info = {}
        for vm, vm_details in vm_info.iteritems():
            pid_info[vm] = fun_test.execute_thread_after(func=poll_untill_le_stops,
                                                         time_in_seconds=5,
                                                         vm_details=vm_details)
        for vm in vm_info:
            fun_test.join_thread(pid_info[vm])
            fun_test.test_assert(True, "Le initiate completed on the VM: {}".format(vm))

    for vm, vm_details in vm_info.iteritems():
        cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":false}' ''' % run_time
        initiate_or_run_le_firewall(cmd, vm_details)
        running = check_if_le_firewall_is_running(vm_details)
        if running:
            fun_test.test_assert(running, "Le started on VM: {}".format(vm))

    fun_test.sleep("For Le-firewall traffic to start", seconds=300)


def kill_le_firewall(vm_details):
    result = False
    try:
        pid = check_if_le_firewall_is_running(vm_details)
        if pid:
            vm_details["handle"].kill_process(pid, signal=9)
            fun_test.log("Process killed successfully on the VM : {}".format(vm_details["name"]))
        else:
            fun_test.log("The process is not running")
        result = True
    except Exception as ex:
        fun_test.log(ex)
    return result


def initiate_or_run_le_firewall(cmd, vm_details):
    vm_details["handle"].enter_sudo()
    vm_details["handle"].command('export WORKSPACE="{}"'.format(vm_details["WORKSPACE"]))
    vm_details["handle"].command('export PYTHONPATH="{}"'.format(vm_details["PYTHONPATH"]))
    vm_details["handle"].command("cd {}".format(vm_details["SCRIPT_PATH"]))
    vm_details["handle"].start_bg_process(cmd)
    vm_details["handle"].command("ps -ef | grep python")
    vm_details["handle"].exit_sudo()


    # vm_details["handle"].destroy()


def check_if_le_firewall_is_running(vm_detail):
    process_id = vm_detail["handle"].get_process_id_by_pattern("run_nu_transit_only.py")
    result = process_id if process_id else False
    return result


def poll_untill_le_stops(vm_details):
    timer = FunTimer(max_time=1200)
    while not timer.is_expired():
        running = check_if_le_firewall_is_running(vm_details)
        if running:
            fun_test.log("Remaining time: {}".format(timer.remaining_time()))
            fun_test.sleep("Before next check", seconds=30)
        else:
            fun_test.log("Le initiated successfully, time taken: {}".format(timer.elapsed_time()))
            break


def reset_the_status(vm_detail):
    vm_detail["handle"].command("cd")

if __name__ == "__main__":
    le_firewall(60, "")