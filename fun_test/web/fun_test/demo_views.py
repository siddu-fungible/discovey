import logging
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
from web.fun_test.demo1_models import LastBgExecution, BgExecutionStatus, StorageController
from web.web_global import initialize_result, api_safe_json_response
from django.http import HttpResponse
from fun_global import RESULTS
import json
from lib.host.linux import Linux
from django.core.exceptions import ObjectDoesNotExist


@csrf_exempt
def home(request):
    return render(request, 'demo1/demo1.html', locals())


def get_new_bg_execution():
    last_execution = LastBgExecution.objects.last()
    if not last_execution:
        l = LastBgExecution()
        l.save()
        last_execution = LastBgExecution.objects.last()
    last_execution.last_bg_execution_id += 1
    last_execution.save()
    last_execution = LastBgExecution.objects.last()
    return last_execution.last_bg_execution_id


def fio_task(bg_execution_id, traffic_context, fio_args):
    f1_ip = traffic_context["f1_ip"]
    tg_ip = traffic_context["tg_ip"]
    tg_mgmt_ip = traffic_context["tg_mgmt_ip"]
    tg_mgmt_ssh_port = traffic_context["tg_mgmt_ssh_port"]
    ns_id = traffic_context["ns_id"]

    bg_execution_id = int(bg_execution_id)
    status = BgExecutionStatus.objects.get(execution_id=bg_execution_id)
    output = ""
    try:
        print "Fio task"
        try:
            linux_obj = Linux(host_ip=tg_mgmt_ip, ssh_username="root", ssh_password="fun123", ssh_port=tg_mgmt_ssh_port)
            # fio_command = 'fio --name=fun_nvmeof --ioengine=fun --rw=readwrite --bs="4096" --size=128k --numjobs=1  --iodepth=8 --do_verify=0 --verify=md5 --verify_fatal=1 --source_ip={} --dest_ip={} --io_queues=1 --nrfiles=1 --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=IO_ONLY'.format(tg_ip, f1_ip)
            fio_command = 'fio --name=fun_nvmeof --ioengine=fun --rw=randrw --bs="4096" --size=128k --numjobs=1  --iodepth=1 --do_verify=0 --verify=md5 --verify_fatal=1 --source_ip={} --dest_ip={} --io_queues=1 --nrfiles=1 --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=IO_ONLY --nsid={} --time_based --runtime=20  --verify_pattern="1232"'.format(
                tg_ip, f1_ip, ns_id)

            print fio_command

            output = linux_obj.command(fio_command)
            output = "cmd: " + fio_command + output


        except Exception as ex:
            print "Exception: " + str(ex)
        app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
        scheduler = app_config.get_background_scheduler()
        print "Fio args: " + str(fio_args)
        scheduler.remove_job(str(bg_execution_id))
        status.status = RESULTS["PASSED"]
        status.output = output
    except Exception as ex:
        status.output = str(ex)
        print "Exception: " + str(ex)
    status.save()
    pass


@csrf_exempt
@api_safe_json_response
def schedule_fio_job(request):
    # fio_params
    # mgmt_ip
    # mgmt_ssh_port
    # fio args
    request_json = json.loads(request.body)
    traffic_context = request_json["traffic_context"]

    print "Scheduler fio job"
    fio_args = {"mgmt_ip": "127.0.0.1"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    scheduler = app_config.get_background_scheduler()
    bg_execution_id = get_new_bg_execution()
    status = BgExecutionStatus(execution_id=bg_execution_id)
    try:
        status.save()
        scheduler.add_job(fio_task, 'interval', seconds=1, args=[bg_execution_id, traffic_context, fio_args], id=str(bg_execution_id))
    except Exception as ex:
        print "Exception:" + str(ex)
    return bg_execution_id


@csrf_exempt
@api_safe_json_response
def job_status(request):
    request_json = json.loads(request.body)
    bg_execution_id = int(request_json["bg_execution_id"])
    result = {}
    result["status"] = -1
    status = BgExecutionStatus.objects.get(execution_id=bg_execution_id)
    result["status"] = status.status
    result["output"] = status.output

    return result


@csrf_exempt
@api_safe_json_response
def add_controller(request):
    request_json = json.loads(request.body)
    ip = request_json["ip"]
    port = int(request_json["port"])
    try:
        StorageController.objects.get(ip=ip, port=port)
    except ObjectDoesNotExist:
        s = StorageController(ip=ip, port=port)
        s.save()

@csrf_exempt
@api_safe_json_response
def set_controller_status(request):
    request_json = json.loads(request.body)
    ip = request_json["ip"]
    port = int(request_json["port"])
    active = request_json["active"]
    try:
        s = StorageController.objects.get(ip=ip, port=port)
        s.active = active
        s.save()
    except ObjectDoesNotExist:
        pass

@csrf_exempt
@api_safe_json_response
def get_controllers(request):
    result = []
    all_objects = StorageController.objects.all()
    for o in all_objects:
        c = {"active": o.active, "ip": o.ip, "port": o.port}
        result.append(c)
    return result


@csrf_exempt
@api_safe_json_response
def get_container_logs(request):
    request_json = json.loads(request.body)
    container_ip = request_json["container_ip"]
    container_ssh_port = request_json["container_ssh_port"]
    container_ssh_username = request_json["container_ssh_username"]
    container_ssh_password = request_json["container_ssh_password"]
    file_name = request_json["file_name"]
    linux_obj = Linux(host_ip=container_ip,
                      ssh_username=container_ssh_username,
                      ssh_port=container_ssh_port, ssh_password=container_ssh_password)
    output = linux_obj.read_file(file_name=file_name)

    return output
