import csv
import os
import Queue
import re
from lib.host.linux import Linux
import csv, glob, random
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
                         ssh_password="#######")


def read_logs(dir):
    log_list = linux_host.list_files(dir)
    for log in log_list:
        if log['info'] != "total":
            linux_host.read_file("{}/{}".format(dir, log['filename']))


def sort_imgs(csv_dir, parent_img_dir):
    # create a consolidated dict of img info
    try:
        list_of_files = os.listdir(csv_dir)
        img_info = get_img_info_dictionary(csv_dir)
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
    except IOError:
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


def get_img_info_dictionary(csv_dir):
    list_of_files = os.listdir(csv_dir)
    img_info_dict = {}
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
                    img_info_dict[row['image_name']] = row
                    img_info_dict[row['image_name']]['dir_name'] = dir_name
    return img_info_dict


def get_untested_imgs(csv_dir, test_img_dir):
    untested_dir = "{}/untested".format(test_img_dir)
    linux_host.create_directory(untested_dir)
    linux_host.sudo_command("rm -f {}/*".format(untested_dir))
    list_of_files = os.listdir(csv_dir)
    img_list = []
    for file_name in list_of_files:
        file_path = "{}/{}".format(csv_dir, file_name)
        with open(file_path) as f:
            data = csv.DictReader(f)
            for row in data:
                img_list.append(row['image_name'])
    img_list = list(set(img_list))
    print "Images already ran: {}".format(len(img_list))
    jpg_dir_lst = linux_host.list_files(test_img_dir)
    for jpg_dir in jpg_dir_lst:
        if jpg_dir['info'] != "total" and jpg_dir['filename'] != "untested":
            jpg_src_dir = "{}/{}".format(test_img_dir, jpg_dir['filename'])
            jpg_lst = linux_host.list_files(jpg_src_dir)
            untested_img_list = []
            for jpg in jpg_lst:
                if jpg['info'] != 'total':
                    if not (jpg['filename'] in img_list):
                        untested_img_list.append(jpg['filename'])
            if len(untested_img_list):
                linux_host.do_blk_cp(src_dir=jpg_src_dir, target_dir=untested_dir, content_lst=untested_img_list)


def parse_f1_logs_gen_csv(f1_log_dir, csv_dir, n_threads=10):
    queue = Queue.Queue()

    f_list = os.listdir(f1_log_dir)
    for f in f_list:
        queue.put("{}/{}".format(f1_log_dir, f))
    for x in xrange(n_threads):
        fun_test.execute_thread_after(time_in_seconds=1 + x,
                                      func=csv_generator,
                                      log_file_queue=queue,
                                      csv_dir=csv_dir)


def csv_generator(log_file_queue, csv_dir):
    while not log_file_queue.empty():
        log_file = log_file_queue.get()
        base_file = log_file.split("/")[-1]
        csv_file = base_file.replace('.txt', ".csv")
        # parse logs
        parsed_log_info_list = parse_logs(log_file)
        local_csv_name = "{}/{}".format(csv_dir, csv_file)
        create_local_csv(csv_name=local_csv_name, result_list=parsed_log_info_list)


def parse_logs(log_path):
    con = open(log_path, 'rb').read()
    a = re.search(r'jpeg_test_many\scompleted\stest', con, re.M & re.I)
    e = re.search(r'function\s\+\soffset', con, re.M & re.I)
    if not a and e:
        fun_test.critical("Crash frame seen in log {}".format(log_path))
        # fun_test.critical("Job {} crashed refer logs".format(log_path))

    log_list = con.split("jpeg_test called to begin")
    img_info_list = []
    for block in log_list:
        img_result = {'accel_comp': False,
                      'accel_dcomp': False,
                      'compress_status': False,
                      'dcompress_status': False,
                      'comp_err_code': None,
                      'dcomp_err_code': None,
                      'image_name': None}
        # image name
        match_image_name = re.search(r"(?<=\()[\w]+\.[\w]+(?=\))", block, re.I & re.M)
        # success in compression
        match_comp_success = re.search('jpeg_test compress verify SUCCESS', block, re.I & re.M)
        # success in decompression
        match_decomp_success = re.search(
            r'jpeg_test\sdecompress\sCOMPLETE\sverify\sSUCCESS|decompress\sverify\sSUCCESS', block, re.I & re.M)
        # error in compresion

        match_com_error = re.search(r'Compression\sfailed\s([\w]*)\s', block, re.I & re.M)
        match_com_error2 = re.search(r'Compression\sfailed\scompletion:\s([\w]*)', block, re.I & re.M)

        # error in decompression
        match_decomp_error = re.search(r'ERROR\sin\sdecompression:([\w]*)', block, re.I & re.M)
        req_sent_to_accel_comp = re.search(r'#{4}Sending.*.Compression#{4}', block, re.I & re.M)
        req_sent_to_accel_dcomp = re.search(r'#{4}Sending.*.Decompression#{4}', block, re.I & re.M)
        crc_match_error = re.search(r'CRC\sMatch\sfailed', block, re.M & re.I)
        data_mismatch = re.search(r'ERROR:\sMismatch\sin', block, re.M & re.I)
        comp_warning = re.search(r'Compression warning\s:\s', block, re.M & re.I)

        if match_image_name:
            img_result['image_name'] = match_image_name.group()
        if match_comp_success:
            img_result['compress_status'] = True
        if match_decomp_success:
            img_result['dcompress_status'] = True
        # error in compresion and error code for that
        if match_com_error:
            img_result['compress_status'] = False
            img_result['comp_err_code'] = match_com_error.group(1)
        if match_com_error2:
            img_result['compress_status'] = False
            img_result['comp_err_code'] = match_com_error2.group(1)

        if req_sent_to_accel_comp:
            img_result['accel_comp'] = True
        if req_sent_to_accel_dcomp:
            img_result['accel_dcomp'] = True

        # error in decompression
        if match_decomp_error:
            img_result['dcompress_status'] = False
            img_result['dcomp_err_code'] = match_decomp_error.group(1)

        if crc_match_error:
            img_result['dcomp_err_code'] = "CRC-MISMATCH"
        if comp_warning:
            img_result['dcomp_err_code'] = "COMP-WARNING"
        if data_mismatch:
            img_result['dcomp_err_code'] = "DATA_MISMATCH"
        if img_result['image_name']:
            img_info_list.append(img_result)
    fun_test.log("parsing completed for log file: {}".format(log_path))
    return img_info_list


def create_local_csv(result_list, csv_name):
    hdr = ['image_name', 'compress_status', 'dcompress_status', 'comp_err_code', 'dcomp_err_code',
           'accel_comp', 'accel_dcomp']
    with open(csv_name, 'wb') as f:  # Just use 'w' mode in 3.x
        w = csv.DictWriter(f, hdr)
        w.writeheader()
        for i in result_list:
            w.writerow(i)
    fun_test.log("Created csv file {}".format(csv_name))


if __name__ == "__main__":
    launch_segrigator(csv_dir="/Users/aameershaikh/projects/IMG_1120_3mb_csv",
                      img_dir="/fuzzer/IMG_1120_3mb",
                      n_threads=35)

    # sort_imgs(csv_dir="/Users/aameershaikh/projects/astronaut_csv",
    #          parent_img_dir="/project/users/fuzzer/qa_jpg/astronaut_fuzzer_imgs/JFIF_SampleJPGImage_500kb")
