from lib.system.fun_test import *
from lib.host.linux import Linux
import re
import requests


class LinuxHelper(Linux):
    def process_is_alive(self, pid):
        status = False
        cmd = "if ps -p {} >/dev/null; then echo True; else echo False; fi".format(pid)
        resp = self.command(cmd)
        if "True" in resp.strip():
            status = True
        return status

    def do_blk_cp(self, src_dir, target_dir, content_lst):
        cp_lst = "/tmp/cp_lst"
        name_str = "\\n".join(content_lst)
        self.command("cd {}".format(src_dir))
        self.command("echo ''>{}".format(cp_lst))
        self.command("echo $'{}'>>{}".format(name_str, cp_lst), timeout=1200)
        self.command("sed -i '/^$/d' {}".format(cp_lst))
        self.sudo_command("cp `cat {}` {}".format(cp_lst, target_dir), timeout=1200)
        fun_test.test_assert_expected(actual=self.command("echo $?").strip(),
                                      expected=0,
                                      message="Copy Successfull")


vnc_host = LinuxHelper(host_ip="fun-on-demand-01",
                       ssh_username="ashaikh",
                       ssh_password="r00t.!@#")

ppaul_host = LinuxHelper(host_ip="10.1.21.206",
                         ssh_username="ashaikh",
                         ssh_password="r00t.!@#")

S1_FUNOS_DIR = "/project/users/hsaladi/FunOS"
S1_FUNSDK_DIR = "/project/users/hsaladi/FunSDK"
S1_LOG_DIR = "/project/users/hsaladi/s1_logs"
S1_CRASH_LOG_DIR = "/project/users/hsaladi/s1_crash_logs"
MAX_PORTIUM_JOBS = 12
s1_workspace_dir = "/project/users/fuzzer/qa_jpg/s1_workspace"
FUNOS_SANITISED = True
REL_VERSION = "rel_"


def run_dir_jpeg_s1(dir_path):
    # get info for all jpeg files in dir
    ppaul_host.enter_sudo()
    file_info = ppaul_host.list_files(path=dir_path)
    jpeg_list = subpack_files(file_info, 30 << 20)
    fun_test.log("Number of Jobs to be scheduled for dir {} is:{}".format(dir_path, len(jpeg_list)))
    global FUNOS_SANITISED
    if not FUNOS_SANITISED:
        FUNOS_SANITISED = True
        make_clean(S1_FUNOS_DIR)
    sched_job_count = 0
    jpeg_list_index = 0
    sched_job_info_list = []
    running_jobs = 0
    while jpeg_list_index < len(jpeg_list):
        sched_job_count = get_total_s1_jobs()
        fun_test.log("Number if jobs sched on Protium: {}".format(sched_job_count))
        if sched_job_count <= MAX_PORTIUM_JOBS and jpeg_list_index < len(
                jpeg_list) and running_jobs <= MAX_PORTIUM_JOBS:
            result = schedule_s1_prot_job(jpeg_list=jpeg_list[jpeg_list_index], dir_path=dir_path)
            fun_test.simple_assert(result['status'], message="Job Scheduled successfully")
            sched_job_info_list.append(result)
            jpeg_list_index += 1
            running_jobs += 1
        else:
            pass
            complete_count = check_job_completed(sched_job_info_list)
            running_jobs -= complete_count
            if running_jobs:
                fun_test.sleep(seconds=120, message="Job in progress")
    print "Completed f1 testing for dir: {}".format(dir_path)


def check_job_completed(jobs_list):
    count = 0
    for i in xrange(len(jobs_list) - 1, -1, -1):
        mail_file = "{}/mail.txt".format(jobs_list[i]['work_dir'])
        log_path = "{}/odp/uartout0.txt".format(jobs_list[i]['work_dir'])
        if vnc_host.check_file_directory_exists(mail_file):
            crash_seen = check_for_crash(log_path)
            if crash_seen:
                vnc_host.cp(source_file_name=log_path,
                            destination_file_name="{0}/s1_log_{1}_{2}.txt".format(S1_CRASH_LOG_DIR,
                                                                                  jobs_list[i]['img_dir'],
                                                                                  jobs_list[i]['job_id']))
                fun_test.critical("Job {} crashed refer logs".format(log_path))
            vnc_host.cp(source_file_name=log_path,
                        destination_file_name="{0}/s1_log_{1}_{2}.txt".format(S1_LOG_DIR,
                                                                              jobs_list[i]['img_dir'],
                                                                              jobs_list[i]['job_id']))
            jobs_list.pop(i)
            count += 1
    return count


def check_for_crash(log_file):
    con = vnc_host.read_file(log_file)
    c = re.search(r'jpeg_test_many\scompleted', con, re.M & re.I)
    if c:
        return False
    e = re.search(r'function\s\+\soffset|Exception|Abort|fatal\sinterrupt|', con, re.M & re.I)
    if e:
        return True


def get_file_size(file_info):
    meta_info = file_info['info']
    size = int(meta_info.split()[4])
    return size


def subpack_files(file_info_list, weight):
    curr_wt = 0
    packed_list = []
    sub_pack_list = []
    for f in file_info_list:
        if f['info'] != 'total':
            if curr_wt < weight:
                curr_wt += get_file_size(f)
                sub_pack_list.append(f['filename'])
            else:
                packed_list.append(sub_pack_list)
                sub_pack_list = [f['filename']]
                curr_wt = get_file_size(f)
    if sub_pack_list:
        packed_list.append(sub_pack_list)
    return packed_list


def schedule_s1_prot_job(dir_path, jpeg_list):
    # create workspace
    result = {'status': False}
    ppaul_host.create_directory(s1_workspace_dir)
    # make_clean(S1_FUNOS_DIR)
    # sanitize
    ppaul_host.sudo_command("rm -f {}/*".format(s1_workspace_dir))
    # copy test images to workspace
    ppaul_host.do_blk_cp(src_dir=dir_path, target_dir=s1_workspace_dir, content_lst=jpeg_list)

    # create list file
    list_file = create_list_file(path=s1_workspace_dir)
    # call run_s1.sh
    build_s1(list_file)
    # call job submit script
    vnc_host._connect()
    cmd = "/home/adikshit/run_s1_protium.py --hardware-version rel_09012019 --priority high_priority --duration 1800 --tags JPEG_S1_PALLADIUM_SCRIPT_SUBMIT_ROOT,early_delete --note \"Dir: {} Imagecount:{}\" --swversion 36474c6 --funosbranch master --funsdkbranch master --email aamir.shaikh@fungible.com /project/users/ashaikh/S1DEFAULT_PROTIUM_rel_09012019/ /project/users/hsaladi/FunOS/build -- app=jpeg_test_many --roundtrip --multithread nthread={} --test-exit-fast  syslog=4 timeout=1800".format(
        dir_path, len(jpeg_list), len(jpeg_list) if len(jpeg_list) < 50 else 50)
    resp = vnc_host.command(cmd)
    vnc_host.command("echo $?")
    fun_test.test_assert_expected(expected=0, actual=vnc_host.command("echo $?").strip(),
                                  message="Build FunOS for S1 Complete")
    m = re.search(r'as\sjob\s(\d*)\sin\sdirectory\s([\S]*)$', resp.strip(), re.M & re.I)

    job_id = m.group(1)
    work_dir = m.group(2)
    work_dir.replace("/project-emu/users/robotpal/SWPalladiumImages/", "/demand/demand/Jobs/")
    fun_test.log("Enqueued job with Job Id: {}, directory: {}".format(job_id, work_dir))
    result['job_id'] = job_id
    result['work_dir'] = m.group(2)
    result['img_dir'] = dir_path.split("/")[-1]
    result['status'] = True
    return result


def make_clean(funos_path):
    ppaul_host.sudo_command("cd {};make clean".format(funos_path))


def create_list_file(path, name=None):
    path = path.rstrip("/")
    ppaul_host.command("cd {}".format(path))
    list_file = "/ppaul/list_dir/{}.list".format(path.split("/")[-1] if not name else name)
    ppaul_host.sudo_command("ls -d -1 $PWD/* > {}".format(list_file))
    ppaul_host.command("cat {}".format(list_file))
    return list_file


def build_s1(list_path):
    ppaul_host.sudo_command("/project/users/hsaladi/ImageStore/includes/runs1.sh  {} {} {}".format(list_path,
                                                                                                   S1_FUNOS_DIR,
                                                                                                   S1_FUNSDK_DIR),
                            timeout=1200)
    fun_test.test_assert_expected(expected=0, actual=ppaul_host.sudo_command("echo $?").strip(),
                                  message="Build FunOS for S1")


def get_total_s1_jobs():
    url = "http://fun-on-demand-01:9004/?format=json"
    total_jobs = 0
    resp = requests.get(url)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        total_jobs = data['stats']['protium_s_jobs']['total_job_count']
    else:
        raise Exception
    return total_jobs


if __name__ == "__main__":
    run_dir_jpeg_s1("/project/users/fuzzer/qa_jpg/astronaut_fuzzer_imgs/JFIF_SampleJPGImage_500kb/comp_pass_decomp_err_CRC-MISMATCH")

    # print get_total_s1_jobs()
