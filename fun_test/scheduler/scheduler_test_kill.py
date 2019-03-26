from fun_settings import *
from scheduler_helper import *
from fun_global import *
import datetime
import dateutil
import dateutil.parser, os


def process_killed_jobs():
    job_files = glob.glob("{}/*{}".format(KILLED_JOBS_DIR, KILLED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        print job_file
        with open(job_file, "r") as f:
            contents = f.read()
            job_id = int(contents)
            print("Killing Job: {}".format(job_id))
        os.remove(job_file)



if __name__ == "__main__":
    kill_job(job_id=521)
