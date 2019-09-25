import csv
import os
import Queue
import re
from lib.system.fun_test import *


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

    def do_blk_mv(self, src_dir, target_dir, content_lst):
        mv_lst = "/tmp/mv_lst"
        name_str = "\\n".join(content_lst)
        self.command("cd {}".format(src_dir))
        self.command("echo ''>{}".format(mv_lst))
        self.command("echo $'{}'>>{}".format(name_str, mv_lst), timeout=90)
        self.command("sed -i '/^$/d' {}".format(mv_lst))
        self.sudo_command("mv `cat {}` {}".format(mv_lst, target_dir), timeout=180)
        '''fun_test.test_assert_expected(actual=self.command("echo $?").strip(),
                                      expected=0,
                                      message="Copy Successfull")'''


linux_host = LinuxHelper(host_ip="10.1.23.85",
                         ssh_username="ashaikh",
                         ssh_password="r00t.!@#")


def read_logs(dir):
    log_list = linux_host.list_files(dir)
    for log in log_list:
        if log['info'] != "total":
            linux_host.read_file("{}/{}".format(dir, log['filename']))


def sort_imgs(csv_dir, parent_img_dir):
    # create a consolidated dict of img info
    try:
        list_of_files = os.listdir(csv_dir)
        img_info = {}
        for file_name in list_of_files:

            file_path = "{}/{}".format(csv_dir, file_name)
            resp = re.search(r'([a-z]*_[\d]*)_', file_name, re.M & re.I)
            dir_name = resp.group(1) if resp else file_name.split(".csv")[0]
            if "untested" in dir_name:
                dir_name = "untested"
            with open(file_path) as f:
                data = csv.DictReader(f)
                for row in data:
                    if row:
                        img_info[row['image_name']] = row
                        img_info[row['image_name']]['dir_name'] = dir_name

        # parse it
        linux_host.enter_sudo()
        for img_file in img_info:
            img_abs_path = "{}/{}/{}".format(parent_img_dir, img_info[img_file]['dir_name'], img_file)
            if not linux_host.check_file_directory_exists(img_abs_path):
                continue
            # c-pass d-pass
            if img_info[img_file]['compress_status'] == 'True' and img_info[img_file]['dcompress_status'] == 'True':
                linux_host.command("mv {} {}/no_err_jpg".format(img_abs_path, parent_img_dir))
            # c-pass d-fail
            if img_info[img_file]['compress_status'] == 'True' and img_info[img_file]['dcompress_status'] == 'False':
                if not linux_host.check_file_directory_exists(
                        "{}/comp_pass_decomp_err_{}".format(parent_img_dir, img_info[img_file]['dcomp_err_code'])):
                    linux_host.command(
                        "mkdir {}/comp_pass_decomp_err_{}".format(parent_img_dir, img_info[img_file]['dcomp_err_code']))
                linux_host.command("mv {} {}/comp_pass_decomp_err_{}".format(img_abs_path, parent_img_dir,
                                                                             img_info[img_file]['dcomp_err_code']))
            # c-fail
            if img_info[img_file]['compress_status'] == 'False':
                if not linux_host.check_file_directory_exists(
                        "{}/comp_err_{}".format(parent_img_dir, img_info[img_file]['comp_err_code'])):
                    linux_host.command(
                        "mkdir {}/comp_err_{}".format(parent_img_dir, img_info[img_file]['comp_err_code']))
                linux_host.command(
                    "mv {} {}/comp_err_{}".format(img_abs_path, parent_img_dir, img_info[img_file]['comp_err_code']))

        print 45
    except:
        print "ex hit"


def segregate_imgs(img_info_queue, parent_dir):
    linux_host = LinuxHelper(host_ip="10.1.23.85",
                             ssh_username="ashaikh",
                             ssh_password="#######")
    linux_host.enter_sudo()
    while not img_info_queue.empty():
        img_name, info = img_info_queue.get()
        img_abs_path = "{}/{}/{}".format(parent_dir, info['dir_name'], img_name)
        if not linux_host.check_file_directory_exists(img_abs_path):
            continue
        # c-pass d-pass
        if info['compress_status'] == 'True' and info['dcompress_status'] == 'True':
            linux_host.command("mv {} {}/no_err_jpg".format(img_abs_path, parent_dir))
        # c-pass d-fail
        if info['compress_status'] == 'True' and info['dcompress_status'] == 'False':
            if not linux_host.check_file_directory_exists(
                    "{}/comp_pass_decomp_err_{}".format(parent_dir, info['dcomp_err_code'])):
                linux_host.command("mkdir {}/comp_pass_decomp_err_{}".format(parent_dir, info['dcomp_err_code']))
            linux_host.command(
                "mv {} {}/comp_pass_decomp_err_{}".format(img_abs_path, parent_dir, info['dcomp_err_code']))
        # c-fail
        if info['compress_status'] == 'False':
            if not linux_host.check_file_directory_exists("{}/comp_err_{}".format(parent_dir, info['comp_err_code'])):
                linux_host.command("mkdir {}/comp_err_{}".format(parent_dir, info['comp_err_code']))
            linux_host.command("mv {} {}/comp_err_{}".format(img_abs_path, parent_dir, info['comp_err_code']))


def launch_segrigator(csv_dir, img_dir, n_threads=1):
    list_of_files = os.listdir(csv_dir)
    img_info = {}
    for file_name in list_of_files:

        file_path = "{}/{}".format(csv_dir, file_name)
        resp = re.search(r'([a-z]*_[\d]*)_', file_name, re.M & re.I)
        dir_name = resp.group(1) if resp else file_name.split(".csv")[0]
        if "untested" in dir_name:
            dir_name = "untested"
        with open(file_path) as f:
            data = csv.DictReader(f)
            for row in data:
                if row:
                    img_info[row['image_name']] = row
                    img_info[row['image_name']]['dir_name'] = dir_name
    img_queue = Queue.Queue()
    for img in img_info:
        img_queue.put((img, img_info[img]))

    for i in xrange(n_threads):
        thread_id = fun_test.execute_thread_after(time_in_seconds=0.5,
                                                  func=segregate_imgs,
                                                  img_info_queue=img_queue,
                                                  parent_dir=img_dir)


if __name__ == "__main__":
    launch_segrigator(csv_dir="/Users/aameershaikh/projects/IMG_1120_3mb_csv",
                      img_dir="/fuzzer/IMG_1120_3mb",
                      n_threads=35)

    # sort_imgs(csv_dir="/Users/aameershaikh/projects/astronaut_csv",
    #          parent_img_dir="/project/users/fuzzer/qa_jpg/astronaut_fuzzer_imgs/JFIF_SampleJPGImage_500kb")
