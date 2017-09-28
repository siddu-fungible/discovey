import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from fun_global import RESULTS
from web.tools.models import Session, F1, Tg, TopologyTask

f1s = [
    {
        "name": "F1",
        "ip": "10.1.20.67"
    },
    {
        "name": "F2",
        "ip": "10.0.0.2"
    },
    {
        "name": "F3",
        "ip": "10.0.0.3"
    }
]


def deploy_topology(session_id):
    print(session_id)
    topology_task = TopologyTask(session_id=session_id)
    topology_task.save()
    # topo.create()
    # parse json and get list of f1s
    for f1 in f1s:
        f1_obj = F1(name=f1["name"], ip=f1["ip"], topology_session_id=session_id)
        try:
            f1_obj.save()
        except Exception as ex:
            print(str(ex))
    topology_task.status = RESULTS["PASSED"]
    topology_task.save()
