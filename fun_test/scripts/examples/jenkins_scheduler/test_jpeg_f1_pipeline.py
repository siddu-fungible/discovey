from lib.system.fun_test import *
from lib.host.linux import Linux
import re


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
        self.command("echo $'{}'>>{}".format(name_str, cp_lst), timeout=90)
        self.command("sed -i '/^$/d' {}".format(cp_lst))
        self.sudo_command("cp `cat {}` {}".format(cp_lst, target_dir), timeout=120)
        fun_test.test_assert_expected(actual=self.command("echo $?").strip(),
                                      expected=0,
                                      message="Copy Successfull")


vnc_host = LinuxHelper(host_ip="fun-on-demand-01",
                       ssh_username="ashaikh",
                       ssh_password="######")

linux_host = LinuxHelper(host_ip="10.1.23.85",
                         ssh_username="ashaikh",
                         ssh_password="#####")

FUNOS_DIR = "/home/ashaikh/projects/FunOS"
F1_LOG_DIR = "/home/ashaikh/projects/f1_logs"
F1_CRASH_LOG_DIR = "/home/ashaikh/projects/f1_crash_logs"
workspace_dir = "/project/users/fuzzer/qa_jpg/f1_workspace"
MAX_F1_JOB_COUNT = 10
F1_WORKSPACE = "/project/users/fuzzer/qa_jpg/f1_workspace"
FUNOS_SANITISED = False


def create_list_file(path, name=None):
    path = path.rstrip("/")
    linux_host.command("cd {}".format(path))
    list_file = "/home/ashaikh/projects/list_files/{}.list".format(path.split("/")[-1] if not name else name)
    linux_host.command("ls -d -1 $PWD/* > {}".format(list_file))
    linux_host.command("cat {}".format(list_file))
    return list_file


def queue_f1(dir_path, img_list):
    result = {'status': False}
    try:
        # create workspace dir
        linux_host.create_directory(F1_WORKSPACE)
        # clean it
        linux_host.sudo_command("rm -f {}/*".format(F1_WORKSPACE))
        # copy test images to workspace
        linux_host.do_blk_cp(src_dir=dir_path, target_dir=F1_WORKSPACE, content_lst=img_list)

        # create list file
        list_file_path = create_list_file(path=F1_WORKSPACE)

        # create app header file
        create_list_hdr(list_file_path)

        # make f1
        make_result = linux_host.sudo_command("cd {};make -j 8 MACHINE=f1 XDATA_LISTS={}".format(FUNOS_DIR,
                                                                                                 list_file_path),
                                              timeout=8 * 60)
        m = re.search(r'STRIP\sbuild/funos-f1.stripped', make_result, re.I & re.M)
        fun_test.test_assert(m, message="make f1")

        # submit job
        try:
            for i in xrange(2):
                resp2 = vnc_host.command(
                    "/home/robotpal/bin/run_f1.py  --duration 3 --hardware-model F1 --email aamir.shaikh@fungible.com {}/build/funos-f1.stripped --tag JPEG_F1_SCRIPT_SUBMIT,early_delete --note LIST:{} -- app=jpeg_test_many --roundtrip syslog=4".format(
                        FUNOS_DIR, dir_path), timeout=90)
                m2 = re.search(r'as\sjob\s(\d*)\sin\sdirectory\s([\S]*)$', resp2.strip(), re.M & re.I)
                if m2:
                    break
        except:
            pass
        # schedule job
        m2 = re.search(r'as\sjob\s(\d*)\sin\sdirectory\s([\S]*)$', resp2.strip(), re.M & re.I)
        fun_test.simple_assert(m, message="Enque f1 job")
        pass
        result['job_id'] = m2.group(1)
        result['work_dir'] = m2.group(2)
        result['img_dir'] = dir_path.split("/")[-1]
        fun_test.log("Enqueued job with Job Id: {}, directory: {}".format(result['job_id'], result['work_dir']))
    except Exception as ex:
        raise ex.message
    return result


def create_list_hdr(list_file):
    linux_host.sudo_command(
        "/project/users/adikshit/ImageStore/includes/list2hdr.sh {}>{}/apps/zipjpg_test.h".format(list_file,
                                                                                                  FUNOS_DIR),
        timeout=60)


def get_file_size(file_info):
    meta_info = file_info['info']
    size = int(meta_info.split()[4])
    return size


def check_jobs_completed(job_info_list):
    count = 0
    for i in xrange(len(job_info_list) - 1, -1, -1):
        mail_file = "{}/mail.txt".format(job_info_list[i]['work_dir'])
        log_path = "{}/odp/uartout0.0.txt".format(job_info_list[i]['work_dir'])
        if vnc_host.check_file_directory_exists(mail_file):
            crash_seen = check_for_crash(log_path)
            if crash_seen:
                fun_test.critical("Job {} crashed refer logs".format(log_path))
                vnc_host.cp(source_file_name=log_path,
                            destination_file_name="{0}/f1_log_{1}_{2}.txt".format(F1_CRASH_LOG_DIR,
                                                                                  job_info_list[i]['img_dir'],
                                                                                  job_info_list[i]['job_id']))
            vnc_host.cp(source_file_name=log_path,
                        destination_file_name="{0}/f1_log_{1}_{2}.txt".format(F1_LOG_DIR,
                                                                              job_info_list[i]['img_dir'],
                                                                              job_info_list[i]['job_id']))
            job_info_list.pop(i)
            count += 1
    return count


def is_robotpal_healthy():
    output = linux_host.read_file("/home/robotpal/ROBOT_CONTROL")
    if output.strip() == "STOP":
        result = False
    else:
        result = True
    return result


def check_for_crash(log_file):
    con = vnc_host.read_file(log_file)
    c = re.search(r'jpeg_test_many\scompleted', con, re.M & re.I)
    if c:
        return False
    e = re.search(r'function\s\+\soffset|Exception|Abort|fatal\sinterrupt|', con, re.M & re.I)
    if e:
        return True


def run_dir_images_f1(dir_path):
    # Initial make clean
    global FUNOS_SANITISED
    fun_test.log("Test Dir: {}".format(dir_path))
    if not FUNOS_SANITISED:
        make_clean()
        FUNOS_SANITISED = True
    # get info for all files in orig-dir
    file_info = linux_host.list_files(path=dir_path)
    file_lst_lst = subpack_files(file_info, 70 << 20)
    running_job_count = 0
    list_index = 0
    sched_job_list = []
    while list_index < len(file_lst_lst) or running_job_count > 0:
        if running_job_count <= MAX_F1_JOB_COUNT and list_index < len(file_lst_lst) and is_robotpal_healthy():
            sched_job_list.append(queue_f1(dir_path=dir_path, img_list=file_lst_lst[list_index]))
            list_index += 1
            running_job_count += 1
            fun_test.sleep("Jobs in queue: {}".format(running_job_count), seconds=0.5)
        else:
            completed_job_count = check_jobs_completed(sched_job_list)
            running_job_count -= completed_job_count
            if not completed_job_count:
                fun_test.sleep(seconds=30, message="{} jobs queued up".format(running_job_count))
    print "Completed f1 testing for dir: {}".format(dir_path)


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


def fetch_jobs():
    fr = open("/Users/aameershaikh/projects/rray_noice_trailing_rst_sched_log").read()
    fl = fr.split("\n")
    for i in fl:
        s = re.search(r'[\w:]*\sEnqueued\s.*.\stag:\sjpg_2_([\d]+).list.*.directory:\s(.*$)', i, re.M & re.I)
        if s:
            print s.group(1), s.group(2)
            log_path = "{}/odp/uartout0.0.txt".format(s.group(2))
            vnc_host.cp(source_file_name=log_path,
                        destination_file_name="{}/jpg_2_{}_f1_log.txt".format(F1_LOG_DIR, s.group(1)))


def make_clean():
    linux_host.sudo_command("cd {};make clean".format(FUNOS_DIR))


if __name__ == "__main__":
    run_dir_images_f1("/project/users/fuzzer/qa_jpg/astronaut_fuzzer_imgs/uncategorized_fuzzer")
