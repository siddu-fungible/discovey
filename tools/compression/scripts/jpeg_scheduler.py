# import sys
# sys.path.append("/Users/fungible/Documents/workspace/Integration/fun_test/")
from lib.host.linux import Linux
import re

class JpegScheduler(Linux):


    CURRENT_JOB_ID = None


    def schedule_job(self):
        pass

    def make_funos(self):
        pass

    def cp_jpeg(self):
        pass

    def get_scheduled_jobs(self):
        pass

class SetupServer(JpegScheduler):
    ASM_GEN_PATH = "/home/aamirqs/aamir_scripts_to_create_jpeg_header_files/"
    FUNOS_PATH = "/home/aamirqs/FunOS"
    JPEG_DATA_PATH = "/home/aamirqs/aamir_scripts_to_create_jpeg_header_files/apps/jpegdata/"

    def create_asm(self,IMAGE_PATH):
        # get all images
        #  if num images> 50
        #  sublist of 50
        #  create .lst file of 50
        #  generate asm
        #  delete 50 files
        #  cp asm , _jpg .
        # result = False
        #,"ls %s > image_store.list"%IMAGE_PATH, - - >
        # "cat image_store.list","./jpeg_asm_multi.sh image_store.list > jpeg_test_asm.h"]

        self.command("cd %s"%ASM_GEN_PATH)
        self.command("rm apps/jpegdata/*")
        self.command("export F1IMAGEPATH='%s'"%IMAGE_PATH)

        image_names = self.command("ls -l %s"%IMAGE_PATH)

        img_info_list = image_names.split("\n")
        images_names_list=[]
        for img_info in img_info_list:
            img_name = img_info[-1]
            images_names_list.append(img_name)

        # images_names_list = filter(lambda a: a!='',images_names_list)
        count_of_images = 0
        self.command("rm -rf image_store.list")
        for image in images_names_list:
            self.command("cat %s >> image_store.list"%image)
            count_of_images += 1
            print image
            if count_of_images == 50:
                count_of_images = 0
                self.command("./jpeg_asm_multi.sh image_store.list > jpeg_test_asm.h")
                self.command("rm -rf image_store.list")

                #/home/aamirqs/aamir_scripts_to_create_jpeg_header_files/apps/jpegdata/*
                #/home/aamirqs/FunOS/apps/jpegdata/
                #  cp asm , _jpg .
                self.command("mv %s*  /home/aamirqs/FunOS/apps/jpegdata/"%)
                self.command("mv jpeg_test_asm.h /home/aamirqs/FunOS/apps/")

                self.command("cd /home/aamirqs/FunOS/")
                self.command("make clean")
                self.command("make -j 8 MACHINE=\"posix\"")
                break


        # get all images
        #  if num images> 50
        #  sublist of 50
        #  create .lst file of 50
        #  generate asm
        #  delete 50 files
        #  cp asm , _jpg .

        result = True
        return result


class RunServer(JpegScheduler):

    def parse_logs(self, log_path):
        pass
    def get_waiting_jobs(self):
        resp = self.command("~cgray/bin/silicon_on_demand.py list")
        match_waiting_jobs = re.search(r'[\d]+ waiting jobs', resp)
        return match_waiting_jobs.group()




if __name__ == '__main__':
    IMAGE_PATH = ""
    # Check for jobs in queue
    # if No jobs present start scheduling one
        # fetch images from dir
        # create asm file
        # copy asm & jpeg to FunOS
        # make f1
        # gzip
        # scp to serverNN
        # schedule using silicon.py return job id
        # poll in 3 mins for job status
        # if job completed parse result
        # sleep 30 mins
    # if Yes sleep 15 mins
    # poll again.




cli.create_asm("/home/aamirqs/ImageStore")