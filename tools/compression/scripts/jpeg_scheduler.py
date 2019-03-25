# import sys
# sys.path.append("/Users/fungible/Documents/workspace/Integration/fun_test/")
import csv
from lib.host.linux import Linux
import re
import time
from lib.system.fun_test import *
import os.path


class JpegScheduler(Linux):
    CURRENT_JOB_ID = None

    def schedule_job(self):
        pass

    def make_funos(self):
        pass

    def get_scheduled_jobs(self):
        pass


class SetupServer(JpegScheduler):
    ASM_GEN_PATH = "/home/aamirqs/aamir_scripts_to_create_jpeg_header_files/"
    ASM_GEN_SCRIPT = "{0}/jpeg_asm_multi.sh".format(ASM_GEN_PATH)
    FUNOS_PATH = "/home/aamirqs/FunOS/"
    F1_BIN_PATH = "{}build/funos-f1.stripped".format(FUNOS_PATH)
    F1_GZ_PATH = "{}.gz".format(F1_BIN_PATH)
    FUNOS_BIN = "/home/ashaikh/funos_bin/"
    JPEG_ASM_PATH = "/home/aamirqs/aamir_scripts_to_create_jpeg_header_files/apps/jpegdata/"
    TMP_IMG_DIR = "/home/aamirqs/tmp_img_dir/"
    TMP_IMG_LST_FILE = "{}/img_file.lst".format(ASM_GEN_PATH)
    ASM_HDR_FILE = "{}/jpeg_test_asm.h".format(ASM_GEN_PATH)

    def file_is_jpg(self, name):
        if re.search(r'\.jpg$', name, re.I & re.M):
            return True
        else:
            return False

    def setup_f1(self, image_path):
        # get all images
        result = False

        threshold_weight = 100 << 20
        try:
            selected_images = self.get_sanitized_img_list(image_path, threshold_weight)
            assert len(selected_images) > 0, "0 Images left in dir"
            if self.check_file_directory_exists(self.TMP_IMG_DIR):
                self.remove_directory_contents(self.TMP_IMG_DIR)
                self.create_directory(self.TMP_IMG_DIR, sudo=False)
            else:
                self.create_directory(self.TMP_IMG_DIR, sudo=False)

            #  create .lst file of 50
            for i in selected_images:
                self.command("mv {0}/{1} {2}".format(image_path, i, self.TMP_IMG_DIR))

            # create list file
            select_img_str = "\n".join(selected_images)
            self.create_file(file_name=self.TMP_IMG_LST_FILE, contents=select_img_str)

            # set F1PATH
            self.command("export F1IMAGEPATH=%s" % self.TMP_IMG_DIR)
            self.command("echo $F1IMAGEPATH")
            # clean apps/jpegdata/ & asm.h
            tmp_app_path = "{}/apps/jpegdata/*".format(self.ASM_GEN_PATH)
            self.command("rm -f {}".format(tmp_app_path))
            self.remove_file(file_name=self.ASM_HDR_FILE)

            #  generate asm
            self.command("cd {}".format(self.ASM_GEN_PATH))

            # move .h nd _jpg files to to FunOS
            self.command("./jpeg_asm_multi.sh img_file.lst >jpeg_test_asm.h")
            jpg_asm_lst = self.list_files(self.JPEG_ASM_PATH)
            for jpg in jpg_asm_lst:
                self.command(
                    "cp {0}/{1} {2}apps/jpegdata/".format(self.JPEG_ASM_PATH, jpg['filename'], self.FUNOS_PATH))
            self.command("cp {0} {1}apps".format(self.ASM_HDR_FILE, self.FUNOS_PATH))
            # make posix
            # resp = self.make_posix()
            # assert resp
            # make f1
            resp = self.make_f1()
            assert resp

            # gzip f1
            assert (self.check_file_directory_exists(self.F1_BIN_PATH))
            resp = self.gzip_f1()
            assert resp
            # scp f1
            resp = self.scp(target_ip=test_nodes['run_server_info']['server_ip'],
                            target_username=test_nodes['run_server_info']['username'],
                            target_password=test_nodes['run_server_info']['password'],
                            source_file_path=self.F1_GZ_PATH,
                            target_file_path=self.FUNOS_BIN)
            assert resp
            # clean jpeg_data
            for jpg in jpg_asm_lst:
                self.remove_file("{0}/apps/jpegdata/{1}".format(self.FUNOS_PATH, jpg['filename']))
            result = True
        except Exception as ex:
            raise ex.message
        return result

    def sanitize_img_name(self, img_name):
        return img_name.replace("-", "_")

    def get_sanitized_img_list(self, path, threshold_weight):
        imgs_info = self.list_files(path)
        img_list = []
        for file in imgs_info:
            size = self.get_file_size(file)
            if self.file_is_jpg(file['filename']) and threshold_weight - size > 0:
                if "-" in file['filename']:
                    file['filename'] = self.create_sanitized_jpg(path, file['filename'])
                threshold_weight -= size
                img_list.append(file['filename'])
        return img_list

    def get_file_size(self, img):
        meta_info = img['info']
        size = int(meta_info.split()[4])
        return size

    def create_sanitized_jpg(self, img_path, img_name, attach_fun_hdr=False):
        result = False
        sanitized_name = img_name.replace("-", "_")
        source_file = img_path.rstrip("/") + "/" + img_name
        target_file = img_path.rstrip("/") + "/" + sanitized_name
        try:
            self.command("mv {0} {1}".format(source_file, target_file))
        except Exception:
            print Exception.message
        return sanitized_name

    def make_f1(self):
        make_cmd = "make -j 8 MACHINE=f1"
        make_result = False
        try:
            self.command("cd {}".format(self.FUNOS_PATH))
            self.command("make clean")
            result = self.command(make_cmd, timeout=5 * 60)
            resp = result.split("\n")[-1]
            m = re.search(r'STRIP\sbuild/funos-f1.stripped', resp, re.I & re.M)
            if m:
                make_result = True
        except Exception:
            print("make f1 failed" + Exception.message)
        return make_result

    def gzip_f1(self):
        resp = False
        funos_stripped_path = "{}build/funos-f1.stripped".format(self.FUNOS_PATH)
        try:
            if self.check_file_directory_exists(funos_stripped_path):
                comp_resp = self.command("gzip {}".format(funos_stripped_path), timeout=45)
                m = re.search(r'rror', comp_resp, re.I & re.M)
                if not m:
                    resp = True
        except Exception:
            print Exception.message
        return resp

    def make_posix(self):
        make_cmd = "make -j 8 MACHINE=posix"
        make_result = False
        try:
            self.command("cd {}".format(self.FUNOS_PATH))
            self.command("make clean")
            result = self.command(make_cmd, timeout=3 * 60)
            resp = result.split("\n")[-1]
            m = re.search(r'STRIP\sbuild/funos-posix.stripped', resp, re.I & re.M)
            if m:
                make_result = True
        except Exception:
            print("make f1 failed" + Exception.message)
        return make_result


class RunServer(JpegScheduler):
    F1_GZ_PATH = "/home/ashaikh/funos_bin/funos-f1.stripped.gz"
    SILICON_ON_DEMAND_PATH = "~cgray/bin/silicon_on_demand.py"
    JOBS_DIR = "/home/cgray/silicon_on_demand/jobs/"
    JOB_STATUS_COMPLETED = 1
    JOB_STATUS_WAITING = 0
    CSV_FILE = "/Users/aameershaikh/projects/Integration/tools/compression/scripts/jpeg_error_images.csv"

    def parse_logs(self, job_id):
        log_path = "{0}{1}/minicom-log.txt".format(self.JOBS_DIR, job_id)
        con = self.read_file(log_path)
        e = re.search(r'exception\sframe', con, re.M & re.I)
        if e:
            print "Crash frame seen in log {}".format(job_id)
            raise Exception("Job {} crashed refer logs".format(job_id))
        list = con.split("jpeg_test called to begin")
        img_info_list = []
        img_count = 0
        for block in list:
            # image name
            image_name = ''
            additional_error_code = ''
            error_code = 'None'
            com_status = "N/A"
            dcomp_status = "N/A"
            match_image_name = re.search(r"(?<=\()[\w]+\.[\w]+(?=\))", block, re.I & re.M)
            # success in compression
            match_comp_success = re.search('jpeg_test compress verify SUCCESS', block, re.I & re.M)
            # success in decompression
            match_decomp_success = re.search('jpeg_test decompress verify SUCCESS', block, re.I & re.M)
            # error in compresion
            match_com_error = re.search(r"(?<=Compression failed completion: )[\w]+", block, re.I & re.M)
            # error in decompression
            match_decomp_error = re.search(r'Decompression failed', block, re.I & re.M)
            if match_image_name:
                image_name = match_image_name.group()
                img_count += 1
            if match_comp_success:
                com_status = "success"
            if match_decomp_success:
                dcomp_status = "success"
            # error in compresion and error code for that
            if match_com_error:
                com_status = "failed"
                error_code = match_com_error.group()
                # print "Compression failed completion: ",match_com_error.group()
            # error in decompression
            if match_decomp_error:
                dcomp_status = "failed"

            if match_decomp_error and (not match_com_error):
                match_error_code = re.search(r'(?<=ERR zip_jpg )"(.*?)"', block, re.I & re.M)
                error_code = match_error_code.group()
                try:
                    match_additonal_error = re.search(r'(?<=zipjpeg_build_indexes:840 )[\w ]+', block, re.I & re.M)
                    additional_error_code = match_additonal_error.group()
                except:
                    print "no addtional error data"
            if image_name:
                dictionary = {"image_name": image_name, 'compression_status': com_status,
                              'decompression_status': dcomp_status, 'error_code': error_code,
                              'Job_ID': job_id}
                if additional_error_code:
                    dictionary["additional_error_code"] = additional_error_code
                img_info_list.append(dictionary)
        print ""
        assert img_count > 0, "Job Id: {0}, Images Parsed: {1}".format(job_id, img_count)
        self.append_csv_file(img_info_list)
        return img_info_list

    def append_csv_file(self, data):
        file_present = os.path.isfile(self.CSV_FILE)
        with open(self.CSV_FILE, "a") as csvfile:
            fields = ['Job_ID', 'image_name', 'compression_status', 'decompression_status', 'error_code',
                      'additional_error_code']
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            if not file_present:
                writer.writeheader()
            writer.writerows(data)
        return

    def get_job_status(self, job_id):
        log = self.command("~cgray/bin/silicon_on_demand.py list")
        completed_job_info = log.split("Last 5 completed jobs ")[-1]
        if job_id in completed_job_info:
            return self.JOB_STATUS_COMPLETED

    def get_waiting_jobs(self):
        resp = self.command("{} list".format(self.SILICON_ON_DEMAND_PATH))
        match_waiting_jobs = re.search(r'==\s(\d*)\swaiting\sjobs', resp, re.M & re.I)
        num_jobs = None
        if match_waiting_jobs:
            num_jobs = int(match_waiting_jobs.group(1))
        return num_jobs

    def wait_for_job_completion(self, job_id):
        run_time = 10 * 60
        job_status = None
        init_time = time.time()
        while time.time() - init_time < run_time:
            job_status = self.JOB_STATUS_COMPLETED if self.get_job_status(
                job_id) == self.JOB_STATUS_COMPLETED else self.JOB_STATUS_WAITING
            if job_status == self.JOB_STATUS_COMPLETED:
                break
            else:
                fun_test.sleep(seconds=2 * 60, message="wait for running job to be completed")
        return job_status

    def schedule_job(self):
        # check f1.gz exists
        self.check_file_directory_exists(self.F1_GZ_PATH)
        cmd_str = "{0} submit {1} --email=aamir.shaikh@fungible.com --timeout=30 -- app=jpeg_test_many --roundtrip".format(
            self.SILICON_ON_DEMAND_PATH, self.F1_GZ_PATH)
        job_id = None
        try:
            resp = self.command(cmd_str)
            m = re.search(r'Submitted\sjobid\s(.*)$', resp, re.M & re.I)
            if m:
                job_id = m.group(1)
        except Exception:
            print Exception.message
        return job_id.strip()


if __name__ == '__main__':
    IMAGE_PATH = "/home/aamirqs/err-0000"
    run_time = 6 * 60 * 60

    dev_server = SetupServer(host_ip=test_nodes['dev_server_info']['server_ip'],
                             ssh_username=test_nodes['dev_server_info']['username'],
                             ssh_password=test_nodes['dev_server_info']['password'])
    run_server = RunServer(host_ip=test_nodes['run_server_info']['server_ip'],
                           ssh_username=test_nodes['run_server_info']['username'],
                           ssh_password=test_nodes['run_server_info']['password'])

    elapsed_time = time.time()

    while time.time() - elapsed_time < run_time:
        num_jobs = run_server.get_waiting_jobs()
        if num_jobs > 0:
            fun_test.sleep(seconds=5 * 60,
                           message="Number of Jobs in queue: {}, wait to schedule next job".format(num_jobs))
            continue
        else:
            dev_server.setup_f1(image_path=IMAGE_PATH)
            curr_job_id = run_server.schedule_job()
            fun_test.sleep(seconds=2 * 60, message="Job being executed")
            resp = run_server.wait_for_job_completion(curr_job_id.strip())
            if resp == run_server.JOB_STATUS_COMPLETED:
                img_test_list = run_server.parse_logs(curr_job_id)
                print img_test_list
