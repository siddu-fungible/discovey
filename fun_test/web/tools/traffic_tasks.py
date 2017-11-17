import os, django, json, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.fun_test.settings")
django.setup()
from fun_global import RESULTS
from fun_settings import *
from web.tools.models import Session, F1, Tg, TrafficTask
from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient
from lib.topology.topology_manager.topo_manager import topo


def start_fio(session_id, f1_record, fio_info):
    traffic_task = TrafficTask.objects.get(session_id=session_id)
    # time.sleep(5)
    print("F1 record: " + str(f1_record))
    logs = []


    topology_obj = topo.Topology()
    pickle_file = WEB_UPLOADS_DIR + "/topology.pkl"
    topology_obj.load(filename=pickle_file)

    info = json.loads(topology_obj.getAccessInfo())
    topology_obj.save(filename=pickle_file)

    print "Info:" + json.dumps(info, indent=4) + ":EINFO"
    tg = None
    tg_found = False
    f1_node = topology_obj.get_node(f1_record["name"])

    if f1_node.tgs:
        for tg in f1_node.tgs:
        #    if tg.node.name == f1_record["name"]:
            tg_found = True
            break
    if not tg_found:
        print("ERROR no TG attached")
        return #tg = topology_obj.attachTG(f1_record["name"])
    print("tg.ip: " + tg.ip)
    block_size = fio_info["block_size"]
    size = fio_info["size"]
    nr_files = fio_info["nr_files"]

    fio_command = "fio --name=fun_nvmeof --ioengine=fun --rw=readwrite --bs={} --size={} --numjobs=1  --iodepth=8 --do_verify=0 --verify=md5 --verify_fatal=1 --source_ip={} --dest_ip={} --io_queues=1 --nrfiles={} --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=IO_ONLY".format(block_size, size, tg.ip, f1_record["dataplane_ip"], nr_files)

    print("FIO command: {}".format(fio_command))
    out = tg.exec_command(fio_command)
    topology_obj.save(filename=pickle_file)
    print("Output:" + str(json.dumps(out, indent=4)))
    traffic_task.status = RESULTS["PASSED"]
    traffic_task.logs = str(out)
    traffic_task.save()

