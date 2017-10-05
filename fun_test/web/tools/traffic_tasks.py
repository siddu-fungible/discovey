import os, django, topo, json, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from fun_global import RESULTS
from fun_settings import *
from web.tools.models import Session, F1, Tg, TrafficTask



def start_fio(session_id, f1_record):
    traffic_task = TrafficTask.objects.get(session_id=session_id)
    time.sleep(5)
    print(f1_record)
    traffic_task.status = RESULTS["PASSED"]
    traffic_task.save()

