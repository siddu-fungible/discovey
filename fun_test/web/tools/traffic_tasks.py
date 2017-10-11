import os, django, topo, json, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from fun_global import RESULTS
from fun_settings import *
from web.tools.models import Session, F1, Tg, TrafficTask
from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient



def start_fio(session_id, f1_record, fio_info, uuid):
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
    if topology_obj.tgs:
        tg = topology_obj.tgs[0]
    else:
        print("ERROR no TG attached")
        return #tg = topology_obj.attachTG(f1_record["name"])
    print("tg.ip: " + tg.ip)
    block_size = fio_info["block_size"]
    size = fio_info["size"]
    nr_files = fio_info["nr_files"]

    fio_command = "fio --name=fun_nvmeof --ioengine=fun --rw=randrw --bs={} --size={} --numjobs=1  --iodepth=8 --do_verify=0 --verify=md5 --verify_fatal=1 --group_reporting --source_ip={} --dest_ip={} --io_queues=4 --nrfiles={} --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=IO_ONLY".format(block_size, size, tg.ip, f1_record["dataplane_ip"], nr_files)

    print("FIO command: {}".format(fio_command))
    out = tg.exec_command(fio_command)
    topology_obj.save(filename=pickle_file)
    print("Output:" + str(out))
    traffic_task.status = RESULTS["PASSED"]
    traffic_task.logs = str(out)
    traffic_task.save()

