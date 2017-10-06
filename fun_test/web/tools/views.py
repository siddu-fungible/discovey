from django.http import HttpResponse
import json
import time, random
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from web.tools.models import Session, F1, Tg, TopologyTask, TrafficTask
from rq import Queue
from redis import Redis
from topology_tasks import deploy_topology
from traffic_tasks import start_fio
from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient
from fun_global import RESULTS
from fun_settings import *
import ikv_tasks
import topo

tgs = [
    {
        "name": "tg1",
        "ip": "11.0.0.1"
    },
    {
        "name": "tg2",
        "ip": "11.0.0.2"
    }
]

@csrf_exempt
def f1_details(request):
    response = {"status": RESULTS["FAILED"]}
    if request.method == 'POST':
        request_json = json.loads(request.body)
        f1_ip = request_json["ip"]
        f1_port = request_json["port"]
        # print(f1_port)
        dpcsh_client_obj = DpcshClient(server_address=f1_ip,
                                       server_port=f1_port)
        result = dpcsh_client_obj.command(command="peek stats")
        if result["status"]:
            response["status"] = RESULTS["PASSED"]
            response["data"] = result["data"]
        else:
            response["error_message"] = result["error_message"]

    return HttpResponse(json.dumps(response))

def f1(request, session_id):
    f1s = []
    f1_records = F1.objects.filter(topology_session_id=int(session_id))
    for f1_record in f1_records:
        f1 = {"name": f1_record.name, "ip": f1_record.ip, "mgmt_ssh_port": f1_record.mgmt_ssh_port, "dataplane_ip": f1_record.dataplane_ip, "dpcsh_port": f1_record.dpcsh_port}
        f1s.append(f1)
    return HttpResponse(json.dumps(f1s))

def traffic_task_status(request, session_id):
    result = {}
    traffic_task = TrafficTask.objects.get(session_id=session_id)
    result["status"] = traffic_task.status
    return HttpResponse(json.dumps(result))

def workflows(request):
    workflows = []
    workflow = {"name": "Create Raw Volume", "id": "create_volume"}
    workflows.append(workflow)
    workflow = {"name": "Attach Volume", "id": "attach_volume"}
    workflows.append(workflow)
    workflow = {"name": "Demo", "id": "demo"}
    workflows.append(workflow)
    workflow = {"name": "Setup Replication", "id": "replication"}
    workflows.append(workflow)
    return HttpResponse(json.dumps(workflows))

def traffic_workflows(request):
    workflows = []
    workflow = {"name": "IKV test", "id": "ikv_test"}
    workflows.append(workflow)
    workflow = {"name": "Traffic", "id": "attach_tg"}
    workflows.append(workflow)
    return HttpResponse(json.dumps(workflows))

def workflow(request, workflow_name):
    workflow_name = workflow_name.lower()
    steps = ["Create volume", "Attach volume"]
    workflow_map = {}
    workflow_map["demo"] = steps

    steps = ["Setup replication", "Validate replication"]
    workflow_map["replication"] = steps

    return HttpResponse(json.dumps(workflow_map[workflow_name]))

@csrf_exempt
def start_workflow_step(request):
    time.sleep(random.randint(0, 5))
    return HttpResponse("Ok")

def tg(request):
    return HttpResponse(json.dumps(tgs))

def index(request):
    return render(request, 'tools_base.html', locals())

def metrics(request, f1_id, metric_name):
    value = {"value": random.randint(0, 10)}
    return HttpResponse(json.dumps(value))

def topology(request):
    session_obj = Session.objects.last()
    session_obj.session_id += 1
    session_obj.save()
    session = {"session_id": session_obj.session_id}
    q = Queue(connection=Redis())
    q.enqueue(deploy_topology, session_obj.session_id)
    return HttpResponse(json.dumps(session))

def topology_cleanup(request):
    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)
    try:
        topology_obj.cleanup()
    except:
        pass
    return HttpResponse("OK")

def topology_status(request, session_id):
    result = {}
    topology_task = TopologyTask.objects.get(session_id=session_id)
    result["status"] = topology_task.status
    return HttpResponse(json.dumps(result))

@csrf_exempt
def upload(request):
    uploaded_file = request.FILES['upload']
    data = uploaded_file.read()
    print data
    return HttpResponse(str(uploaded_file.data))

def _get_f1_record(topology_session_id, f1_id):
    f1_record = F1.objects.get(topology_session_id=int(topology_session_id), name=f1_id)
    return f1_record


@csrf_exempt
def ikv_put(request, topology_session_id, f1_id):
    uploaded_file = request.FILES['upload']
    bite = uploaded_file.read()
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    key_hex = ikv_tasks.ikv_put(bite, server_ip, server_port)
    return HttpResponse(key_hex)


def ikv_get(request, key_hex, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    
    return HttpResponse(ikv_tasks.ikv_get(key_hex=key_hex, server_ip=server_ip, server_port=server_port))

@csrf_exempt
def fio(request, topology_session_id, f1_id):
    if TrafficTask.objects.filter(session_id=topology_session_id).exists():
        task = TrafficTask.objects.filter(session_id=topology_session_id).delete()

    traffic_task = TrafficTask(session_id=topology_session_id)
    traffic_task.save()
    request_json = json.loads(request.body)
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=request_json['f1']['name'])
    q = Queue(connection=Redis())


    f1_info = {}
    f1_info["name"] = f1_record.name
    f1_info["ip"] = f1_record.ip
    f1_info["dataplane_ip"] = f1_record.dataplane_ip
    f1_info["dpcsh_port"] = f1_record.dpcsh_port

    q.enqueue(start_fio, topology_session_id, f1_info)
    return HttpResponse("OK")

