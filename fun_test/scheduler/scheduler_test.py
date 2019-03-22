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
    suite_path = "test2.json"
    build_url = "http://dochub.fungible.local/doc/jenkins/funos/latest/"
    schedule_in_minutes = 1


    #queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=schedule_in_minutes, repeat=True)
    schedule_in_minutes = 2
    #queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=schedule_in_minutes, repeat=True)
    #queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=1, repeat=True)
    # queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=60, repeat=True)
    #queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=0, repeat_in_minutes=1)


    #queue_job(suite_path=suite_path, build_url=build_url)# , schedule_in_minutes=schedule_in_minutes, repeat=True)
    # queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=0, repeat_in_minutes=2)# , schedule_in_minutes=schedule_in_minutes, repeat=True)
    #queue_job(suite_path=suite_path, build_url=build_url, schedule_in_minutes=2)# , schedule_in_minutes=schedule_in_minutes, repeat=True)


    # process_killed_jobs()

    queue_job2(suite_path=suite_path,
               build_url=build_url,
               scheduling_type="today",
               requested_days=["wednesday"],
               requested_hour=1,
               requested_minute=16,
               tz_string="PST",
               repeat_in_minutes=3,
               tags=["john"], email_list=["john.abraham@fungible.com"], email_on_fail_only=True, environment=None)