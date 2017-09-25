from django.http import HttpResponse
import json
import time, random
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from web.tools.models import Session, F1, Tg, TopologyTask
from rq import Queue
from redis import Redis
from topology_tasks import deploy_topology

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




def f1(request, session_id):
    f1s = []
    f1_records = F1.objects.filter(topology_session_id=int(session_id))
    for f1_record in f1_records:
        f1 = {"name": f1_record.name, "ip": f1_record.ip}
        f1s.append(f1)
    return HttpResponse(json.dumps(f1s))

def workflows(request):
    workflows = []
    workflow = {"name": "Create Volume", "id": "create_volume"}
    workflows.append(workflow)
    workflow = {"name": "Attach Volume", "id": "attach_volume"}
    workflows.append(workflow)
    workflow = {"name": "Demo", "id": "demo"}
    workflows.append(workflow)
    workflow = {"name": "Replication", "id": "replication"}
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

def topology_status(request, session_id):
    result = {}
    topology_task = TopologyTask.objects.get(session_id=session_id)
    result["status"] = topology_task.status
    return HttpResponse(json.dumps(result))