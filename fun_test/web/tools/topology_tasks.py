import os, django, topo, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from fun_global import RESULTS
from fun_settings import *
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


    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    '''
    if os.path.exists(pickle_file):
        topology_obj = topo.Topology()
        topology_obj.load(filename=pickle_file)
        try:
            topology_obj.cleanup()
        except:
            pass
        try:
            os.remove(pickle_file)
        except:
            pass
    '''
    if not os.path.exists(pickle_file):
    
        topology_obj = topo.Topology()
        topology_obj.create(2, 4, 4)
        info = json.loads(topology_obj.getAccessInfo())
        topology_obj.save(filename=pickle_file)
    else:
        topology_obj = topo.Topology()
        topology_obj.load(filename=pickle_file)
        info = json.loads(topology_obj.getAccessInfo())
        topology_obj.save(filename=pickle_file)
         
    print "Info:" + json.dumps(info, indent=4) + ":EINFO"
    for f1_name, f1_info in info["F1"].items():
        f1_obj = F1(name=f1_name, ip=f1_info["mgmt_ip"], dpcsh_port=f1_info["dpcsh_port"], mgmt_ssh_port=f1_info["mgmt_ssh_port"], dataplane_ip=f1_info["dataplane_ip"], topology_session_id=session_id)
        try:
            f1_obj.save()
        except Exception as ex:
            print(str(ex))
            

    '''
    for f1 in f1s:
        f1_obj = F1(name=f1["name"], ip=f1["ip"], topology_session_id=session_id, dpcsh_port=5001)
        try:
            f1_obj.save()
        except Exception as ex:
            print(str(ex))

    '''

    topology_task.status = RESULTS["PASSED"]
    topology_task.save()
