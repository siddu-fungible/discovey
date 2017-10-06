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



    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)

    info = json.loads(topology_obj.getAccessInfo())
    topology_obj.save(filename=pickle_file)

    print "Info:" + json.dumps(info, indent=4) + ":EINFO"

    tg = topology_obj.attachTG(f1_record["name"])
    out = tg.exec_command('fio --help')
    topology_obj.save(filename=pickle_file)
    print("Output:" + str(out))
    traffic_task.status = RESULTS["PASSED"]
    traffic_task.save()

