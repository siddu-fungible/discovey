import logging
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
from web.fun_test.demo1_models import LastBgExecution, BgExecutionStatus
from web.web_global import initialize_result, api_safe_json_response
from django.http import HttpResponse
from fun_global import RESULTS

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


def fio_task(bg_execution_id, fio_args):
    bg_execution_id = int(bg_execution_id)
    status = BgExecutionStatus.objects.get(execution_id=bg_execution_id)
    try:
        print "Fio task"
        app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
        scheduler = app_config.get_background_scheduler()
        print "Fio args: " + str(fio_args)
        scheduler.remove_job(str(bg_execution_id))
        status.status = RESULTS["PASSED"]
    except Exception as ex:
        status.output = str(ex)
    status.save()
    pass


@csrf_exempt
@api_safe_json_response
def schedule_fio_job(request):
    # fio_params
    # mgmt_ip
    # mgmt_ssh_port
    # fio args
    print "Scheduler fio job"
    fio_args = {"mgmt_ip": "127.0.0.1"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    scheduler = app_config.get_background_scheduler()
    bg_execution_id = get_new_bg_execution()
    status = BgExecutionStatus(execution_id=bg_execution_id)
    status.save()
    scheduler.add_job(fio_task, 'interval', seconds=1, args=[bg_execution_id, fio_args], id=str(bg_execution_id))
    return HttpResponse("Ok")