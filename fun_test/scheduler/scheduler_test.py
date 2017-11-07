from fun_settings import *
from scheduler_helper import *
from fun_global import *
import datetime
import dateutil
import dateutil.parser

if __name__ == "__main__":
    suite_path = "test2.json"
    build_url = "url"
    schedule_in_minutes = 1


    d1 = get_current_time()
    d1s = d1.isoformat()
    print d1s
    d2 = d1 + datetime.timedelta(minutes=0)
    print d2

    d3 = dateutil.parser.parse(d1s)
    # d3 = datetime.datetime.strptime(d1s, "%Y-%m-%d %H:%M:%S.%f")
    #d3 = get_a_time(d3)
    print d1, d3


    print d1 == d3



    queue_job(suite_path=suite_path, build_url=build_url) #, schedule_in_minutes=schedule_in_minutes)