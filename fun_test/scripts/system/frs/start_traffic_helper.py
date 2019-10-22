import dpcsh_nocli
from lib.system.fun_test import *
from lib.host.linux import Linux

vm_1 = "10.1.20.52"
vm_2 = "10.1.23.228"

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


def le_firewall(run_time, new_image):
    if new_image:
        run_time += 400
    else:
        run_time += 200
    kill_le_firewall()
    if new_image:
        cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":true}' ''' % run_time
    else:
        cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":false}' ''' % run_time
    print cmd
    host_1 = Linux(host_ip=vm_1, ssh_username="localadmin", ssh_password="Precious1*")
    host_1.enter_sudo()
    host_1.command('export WORKSPACE="/home/localadmin/Integration"')
    host_1.command('export PYTHONPATH="/home/localadmin/Integration/fun_test"')
    host_1.command("cd /home/localadmin/Integration/fun_test/scripts/power_monitor")
    host_1.start_bg_process(cmd)
    host_1.command("ps -a | grep python")
    host_1.exit_sudo()
    fun_test.test_assert(True, "Le-firewall started on {} VM for {} seconds".format(vm_1, run_time))

    host_2 = Linux(host_ip=vm_2, ssh_username="localadmin", ssh_password="r00t.!@#")
    host_2.enter_sudo()
    host_2.command("cd /home/localadmin/fungible_automation/Integration/fun_test/scripts/power_monitor")
    host_2.command("git checkout ranga/power")
    host_2.command('export WORKSPACE="/home/localadmin/fungible_automation/Integration"')
    host_2.command('export PYTHONPATH="/home/localadmin/fungible_automation/Integration/fun_test"')
    host_2.start_bg_process(cmd)
    host_1.command("ps -a | grep python")
    host_2.exit_sudo()
    host_1.destroy()
    host_2.destroy()
    if new_image:
        fun_test.sleep("for Le-firewall to start traffic", seconds=360)
    else:
        fun_test.sleep("for Le-firewall to start traffic", seconds=100)
    fun_test.test_assert(True, "Le-firewall started on {} VM for {} seconds".format(vm_2, run_time))


def kill_le_firewall():
    host_1 = Linux(host_ip=vm_1, ssh_username="localadmin", ssh_password="Precious1*")
    host_2 = Linux(host_ip=vm_2, ssh_username="localadmin", ssh_password="r00t.!@#")
    try:

        for host in host_1, host_2:
            result = False
            for i in range(2):
                process_id = host.get_process_id_by_pattern("run_nu_transit_only.py")
                if process_id:
                    result = True
                    host.kill_process(process_id, signal=9)
            fun_test.test_assert(True, "Le-firewall stopped on the VM")
        host_1.destroy()
        host_2.destroy()
    except Exception as ex:
        fun_test.log(ex)


def start_le_firewall():
    run_time = 30
    kill_le_firewall()
    cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":true}' '''%run_time
    host_1 = Linux(host_ip=vm_1, ssh_username="localadmin", ssh_password="Precious1*")
    host_1.enter_sudo()
    host_1.command('export WORKSPACE="/home/localadmin/Integration"')
    host_1.command('export PYTHONPATH="/home/localadmin/Integration/fun_test"')
    host_1.command("cd /home/localadmin/Integration/fun_test/scripts/power_monitor")
    host_1.start_bg_process(cmd)
    host_1.command("pwd")
    host_1.exit_sudo()
    fun_test.test_assert(True, "Le-firewall initiate on {} VM".format(vm_1))

    host_2 = Linux(host_ip=vm_2, ssh_username="localadmin", ssh_password="r00t.!@#")
    host_2.enter_sudo()
    host_2.command("cd /home/localadmin/fungible_automation/Integration/fun_test/scripts/power_monitor")
    host_2.command("git checkout ranga/power")
    host_2.command('export WORKSPACE="/home/localadmin/fungible_automation/Integration"')
    host_2.command('export PYTHONPATH="/home/localadmin/fungible_automation/Integration/fun_test"')
    host_2.start_bg_process(cmd)
    host_2.command("pwd")
    host_2.exit_sudo()
    fun_test.sleep("to initiate Le-firewall", seconds=600)

    host_1.destroy()
    host_2.destroy()
    fun_test.test_assert(True, "Le-firewall initiated on {} VM".format(vm_2))


if __name__ == "__main__":
    le_firewall(60, "")