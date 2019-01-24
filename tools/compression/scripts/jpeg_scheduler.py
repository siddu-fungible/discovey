import sys

sys.path.append("/Users/aameershaikh/projects/Integration/fun_test")
from lib.host.linux import Linux

class JpegScheduler():

    CURRENT_JOB_ID = None

    def __init__(self):
        pass

    def schedule_job(self):
        pass

    def make_funos(self):
        pass

    def cp_jpeg(self):
        pass

    def create_asm(self):
        pass

    def get_scheduled_jobs(self):
        pass

    def parse_logs(self, log_path):
        pass


if __name__ == '__main__':
    print "Mian"
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

cli = Linux(host_ip=test_nodes['make_server_info']['server_ip'],
            ssh_username=test_nodes['make_server_info']['username'],
            ssh_password=test_nodes['make_server_info']['password'])
resp = cli.command("ls $HOME")

for i in resp.split(" "):
    if i.strip():
        print i
