from django.http import HttpResponse
import json, uuid, os
import time, random
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from web.tools.models import Session, F1, Tg, TopologyTask, TrafficTask, IkvVideoTask
from rq import Queue
from redis import Redis
from web.tools.topology_tasks import deploy_topology
from web.tools.traffic_tasks import start_fio
from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient
from fun_global import RESULTS
from fun_settings import *
import web.tools.ikv_tasks as ikv_tasks
from lib.topology.topology_manager.topo_manager import topo
from collections import OrderedDict

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
    f1s = sorted(f1s, key=lambda f1: f1["name"])
    # f1s.reverse()
    return HttpResponse(json.dumps(f1s))

def traffic_task_status(request, session_id):
    result = {}
    traffic_task = TrafficTask.objects.get(session_id=session_id)
    result["status"] = traffic_task.status
    result["logs"] = traffic_task.logs
    return HttpResponse(json.dumps(result))

def ikv_video_task_status(request, session_id):
    result = {}
    ikv_video_task = IkvVideoTask.objects.get(session_id=session_id)
    result["status"] = ikv_video_task.status
    result["logs"] = ikv_video_task.logs
    return HttpResponse(json.dumps(result))

def workflows(request):
    workflows = []
    workflow = {"name": "Create Raw Volume", "id": "create_volume"}
    workflows.append(workflow)
    workflow = {"name": "Export Volume", "id": "attach_volume"}
    workflows.append(workflow)
    # workflow = {"name": "Set IP config", "id": "set_ip_cfg"}
    # workflows.append(workflow)
    workflow = {"name": "Import Remote Volume", "id": "create_rds_volume"}
    workflows.append(workflow)
    workflow = {"name": "Create Replica Volume", "id": "create_replica_volume"}
    workflows.append(workflow)
    workflow = {"name": "Fault Injection", "id": "fault_injection"}
    workflows.append(workflow)
    return HttpResponse(json.dumps(workflows))

def traffic_workflows(request):
    workflows = []
    workflow = {"name": "Key-value store test", "id": "ikv_test"}
    workflows.append(workflow)
    workflow = {"name": "Attach Traffic generator", "id": "attach_tg"}
    workflows.append(workflow)
    workflow = {"name": "Send Traffic", "id": "send_traffic"}
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
    q.enqueue(deploy_topology, session_obj.session_id, timeout=600)
    return HttpResponse(json.dumps(session))

def topology_cleanup(request):
    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)
    try:
        topology_obj.cleanup()
        os.remove(pickle_file)
    except:
        pass
    try:
        os.remove(pickle_file)
    except Exception as ex:
        print(str(ex))
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
def ikv_video_put(request, topology_session_id, f1_id):
    if IkvVideoTask.objects.filter(session_id=topology_session_id).exists():
        task = IkvVideoTask.objects.filter(session_id=topology_session_id).delete()

    ikv_video_task = IkvVideoTask(session_id=topology_session_id)
    ikv_video_task.save()
    uploaded_file = request.FILES['upload']
    bite = uploaded_file.read()
    video_file = WEB_UPLOADS_DIR + "/video.mp4" #TODO
    with open(video_file, 'wb') as outfile:
        outfile.write(bite) 
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    f1_info = {}
    f1_info["name"] = f1_record.name
    f1_info["ip"] = f1_record.ip
    f1_info["dataplane_ip"] = f1_record.dataplane_ip
    f1_info["dpcsh_port"] = f1_record.dpcsh_port

   
    q = Queue(connection=Redis())
    q.enqueue(ikv_tasks.ikv_video_put, f1_info=f1_info, session_id=topology_session_id)
    # key_hex = ikv_tasks.ikv_put(bite, server_ip, server_port)
    return HttpResponse("Ok")

@csrf_exempt
def ikv_put(request, topology_session_id, f1_id):
    uploaded_file = request.FILES['upload']
    bite = uploaded_file.read()
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    key_hex = ikv_tasks.ikv_put(bite, server_ip, server_port)
    return HttpResponse(key_hex)

def ikv_video_get(request, topology_session_id, f1_id, key_hex):
    key_hex = key_hex.strip(".ts")
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    ba = ikv_tasks.ikv_get(key_hex=key_hex, server_ip=server_ip, server_port=server_port, get_bytes=True) 
    #with open(WEB_UPLOADS_DIR + "/" + key_hex, "wb") as outfile:
    #    outfile.write(ba)
    return HttpResponse(str(ba),  content_type="video/mp2t")

def ikv_get(request, key_hex, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    
    return HttpResponse(ikv_tasks.ikv_get(key_hex=key_hex, server_ip=server_ip, server_port=server_port))

@csrf_exempt
def attach_tg(request, topology_session_id, f1_id):
    logs = []
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip


    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)

    info = json.loads(topology_obj.getAccessInfo())
    topology_obj.save(filename=pickle_file)


    tg = None
    tg_found = False
    print("F1 Name:" + f1_record.name)
    f1_node = topology_obj.get_node(f1_record.name)
    if f1_node.tgs:
        print("Searching for {} Found".format(f1_id))
        for tg in f1_node.tgs:
            if tg.node.name == f1_id:
                print("Found {} in tg list".format(f1_id))
                tg_found = True
                break
    if not tg_found:
        print("No TG found, attaching a new one")
        tg = topology_obj.attachTG(f1_id)
    print("**** tg.ip: " + tg.ip)
    topology_obj.save(filename=pickle_file)


    # result["logs"] = ["Attached TG: {}".format(tg.ip)]
    return HttpResponse(tg.ip)

'''
@csrf_exempt
def attach_tg(request, topology_session_id, f1_id):
    logs = []
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)

    request_json = json.loads(request.body)
    uuid = request_json["uuid"]
    this_uuid = uuid

    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)

    info = json.loads(topology_obj.getAccessInfo())
    topology_obj.save(filename=pickle_file)

    print "Info:" + json.dumps(info, indent=4) + ":EINFO"


    tg = None
    tg_found = False
    print("F1 Name:" + f1_record.name)
    f1_node = topology_obj.get_node(f1_record.name)
    #print f1_node.__dict__
    if f1_node.tgs:
        print("Searching for {} Found".format(f1_id))
        for tg in f1_node.tgs:
            if tg.node.name == f1_id:
                print("Found {} in tg list".format(f1_id))
                tg_found = True
                break
    if not tg_found:
        print("No TG found, attaching a new one")
        tg = topology_obj.attachTG(f1_id)
    print("**** tg.ip: " + tg.ip)
    topology_obj.save(filename=pickle_file)


    create_dict = {"class": "controller",
                   "opcode": "ATTACH",
                   "params": {"huid": 0,
                              "ctlid": 0,
                              "fnid": 5,
                              "nsid": 1,   # TODO
                              "uuid": this_uuid,
                              "remote_ip": tg.ip}}
    command = "storage {}".format(json.dumps(create_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    logs.append("command result: " + json.dumps(result, indent=4))
    print("attach command result: " + str(result))


    if result["status"]:
        data = result["data"]
    
    if (not result["status"]) and (not result["data"]):
            result["status"] = True
    print("create command result: " + str(result))
    logs.append("create command result: " + json.dumps(result, indent=4))
    result["logs"] = logs
    return HttpResponse(json.dumps(result))
'''


@csrf_exempt
def fio(request, topology_session_id, f1_id):
    if TrafficTask.objects.filter(session_id=topology_session_id).exists():
        task = TrafficTask.objects.filter(session_id=topology_session_id).delete()

    traffic_task = TrafficTask(session_id=topology_session_id)
    traffic_task.save()
    request_json = json.loads(request.body)
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    q = Queue(connection=Redis())

    f1_info = {}
    f1_info["name"] = f1_record.name
    f1_info["ip"] = f1_record.ip
    f1_info["dataplane_ip"] = f1_record.dataplane_ip
    f1_info["dpcsh_port"] = f1_record.dpcsh_port

    fio_info = {}
    fio_info["block_size"] = request_json["block_size"]
    fio_info["size"] = request_json["size"]
    fio_info["nr_files"] = request_json["nr_files"]

    q.enqueue(start_fio, topology_session_id, f1_info, fio_info)
    return HttpResponse("OK")


@csrf_exempt
def create_blt_volume(request, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)

    request_json = json.loads(request.body)

    logs = []

    # ctrl_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": f1_record.ip}}
    ctrl_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": f1_record.dataplane_ip}}
    command = "storage {}".format(json.dumps(ctrl_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    print("ctrl command result: " + str(result))
    logs.append("ctrl command result: " + json.dumps(result, indent=4))

    capacity = request_json["capacity"]
    block_size = request_json["block_size"]
    name = request_json["name"]
    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]

    create_dict = OrderedDict()
    create_dict["class"] = "volume"
    create_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
    create_dict["params"] = OrderedDict()
    create_dict["params"]["type"] = "VOL_TYPE_BLK_LOCAL_THIN"
    create_dict["params"]["capacity"] = capacity
    create_dict["params"]["block_size"] = block_size
    create_dict["params"]["uuid"] = this_uuid
    create_dict["params"]["name"] = name
    command = "storage {}".format(json.dumps(create_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    data = {}
    if result["status"]:
        data = result["data"]
    print("create command result: " + str(result))
    logs.append("create command result: " + json.dumps(result, indent=4))
    result["logs"] = logs
    return HttpResponse(json.dumps(result))


@csrf_exempt
def create_rds_volume(request, topology_session_id, f1_id):
    logs = []
    print("Create RDS volume")
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)

    ctrl_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": f1_record.dataplane_ip}}
    command = "storage {}".format(json.dumps(ctrl_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    print("ctrl command result: " + str(result))
    logs.append("command result: " + json.dumps(result, indent=4))

    request_json = json.loads(request.body)
    capacity = request_json["capacity"]
    block_size = request_json["block_size"]
    name = request_json["name"]
    remote_ip = request_json["remote_ip"]
    remote_nsid = request_json["remote_nsid"]
    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]

    create_dict = {"class": "volume",
                   "opcode": "VOL_ADMIN_OPCODE_CREATE",
                   "params": {"type": "VOL_TYPE_BLK_RDS",
                              "capacity": capacity,
                              "block_size": block_size,
                              "uuid": this_uuid,
                              "name": name,
                              "remote_ip": remote_ip,
                              "remote_nsid": remote_nsid}}

    command = "storage {}".format(json.dumps(create_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    logs.append("command result: " + json.dumps(result, indent=4))
    print("create command result: " + str(result))
    if result["status"]:
        i = result["data"]
    result["logs"] = logs
    return HttpResponse(json.dumps(result))

@csrf_exempt
def set_ip_cfg(request, topology_session_id, f1_id):
    logs = []
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    ctrl_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": f1_record.dataplane_ip}}
    command = "storage {}".format(json.dumps(ctrl_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    print("ctrl command result: " + str(result))
    logs.append("command result: " + json.dumps(result, indent=4))
    result["logs"] = logs
    return HttpResponse(json.dumps(result))

@csrf_exempt
def create_replica_volume(request, topology_session_id, f1_id):
    logs = []
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)

    request_json = json.loads(request.body)
    capacity = request_json["capacity"]
    block_size = request_json["block_size"]
    name = request_json["name"]
    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
    pvol_id = request_json["pvol_id"]

    create_dict = {"class": "volume",
                   "opcode": "VOL_ADMIN_OPCODE_CREATE",
                   "params": {"type": "VOL_TYPE_BLK_REPLICA",
                              "capacity": capacity,
                              "block_size": block_size,
                              "uuid": this_uuid,
                              "name": name,
                              "min_replicas_insync": 1,
                              "pvol_type": "VOL_TYPE_BLK_RDS",
                              "pvol_id": pvol_id}}
    command = "storage {}".format(json.dumps(create_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    logs.append("command result: " + json.dumps(result, indent=4))
    print("replica command result: " + str(result))
    if result["status"]:
        i = result["data"]
    result["logs"] = logs
    return HttpResponse(json.dumps(result))


@csrf_exempt
def fault_injection(request, topology_session_id, f1_id):
    logs = []

    request_json = json.loads(request.body)
    this_uuid = request_json["uuid"]

    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    inject_dict = {"class":"volume", "opcode":"VOL_ADMIN_OPCODE_INJECT_FAULT", "params": {"uuid" : this_uuid}}
    command = "storage {}".format(json.dumps(inject_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command)
    logs.append("command result: " + json.dumps(result, indent=4))
    print("attach command result: " + str(result))
    if result["status"]:
        i = result["data"]
    result["logs"] = logs
    return HttpResponse(json.dumps(result))


@csrf_exempt
def attach_volume(request, topology_session_id, f1_id):
    logs = []
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)

    request_json = json.loads(request.body)
    this_uuid = request_json["uuid"]
    nsid = request_json["nsid"]
    remote_ip = request_json["remote_ip"]

    create_dict = {"class": "controller",
                   "opcode": "ATTACH",
                   "params": {"huid": 0,
                              "ctlid": 0,
                              "fnid": 5,
                              "nsid": nsid,
                              "uuid": this_uuid,
                              "remote_ip": remote_ip}}
    command = "storage {}".format(json.dumps(create_dict))
    logs.append("Sending: " + command)
    result = dpcsh_client.command(command=command, expected_command_duration=4)
    logs.append("command result: " + json.dumps(result, indent=4))
    print("attach command result: " + str(result))
    if result["status"]:
        i = result["data"]
    if (not result["status"]) and (not result["data"]):
            result["status"] = True
    result["logs"] = logs
    return HttpResponse(json.dumps(result))

def storage_volumes(request, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    return HttpResponse(json.dumps(dpcsh_client.command(command="peek storage/volumes")))

def storage_stats(request, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    result = dpcsh_client.command(command="enable_counters")
    # print("Repvol on {} {}".format(server_ip, server_port))
    #result = dpcsh_client.command(command="peek stats/repvol/0")
    # if result["status"]:
    #    print(json.dumps(result["data"], indent=4))

    result = dpcsh_client.command(command="peek storage/volumes")
    response = {"status": RESULTS["FAILED"]}
    if result["status"]:
        response["status"] = RESULTS["PASSED"]
        response["data"] = result["data"]
        print(json.dumps(response["data"], indent=4))
    else:
        response["error_message"] = result["error_message"]
    return HttpResponse(json.dumps(response))

def storage_repvol_stats(request, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    result = dpcsh_client.command(command="enable_counters")
    result = dpcsh_client.command(command="peek stats/repvol/0")
    response = {"status": RESULTS["FAILED"]}
    if result["status"]:
        response["status"] = RESULTS["PASSED"]
        response["data"] = result["data"]
        print(json.dumps(response["data"], indent=4))
    else:
        response["error_message"] = result["error_message"]
    return HttpResponse(json.dumps(response))


def ikv_stats(request, topology_session_id, f1_id):
    f1_record = _get_f1_record(topology_session_id=topology_session_id, f1_id=f1_id)
    server_ip = f1_record.ip
    server_port = f1_record.dpcsh_port
    dpcsh_client = DpcshClient(server_address=server_ip, server_port=server_port)
    result = dpcsh_client.command(command="enable_counters")
    result = dpcsh_client.command(command="peek stats/likv")
    response = {"status": RESULTS["FAILED"]}
    if result["status"]:
        response["status"] = RESULTS["PASSED"]
        response["data"] = result["data"]
        print(json.dumps(response["data"], indent=4))
    else:
        response["error_message"] = result["error_message"]
    return HttpResponse(json.dumps(response))
