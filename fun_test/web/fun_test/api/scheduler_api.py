from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import SchedulerDirective, SchedulerInfo
from scheduler.scheduler_global import SchedulerDirectiveTypes
from scheduler.scheduler_global import SchedulerStates
from scheduler.scheduler_helper import pause, unpause
import json


@csrf_exempt
@api_safe_json_response
def directive(request):
    if request.method == "POST":
        request_json = json.loads(request.body)
        directive = request_json.get("directive", None)
        if directive is not None:
            if directive == SchedulerDirectiveTypes.PAUSE_QUEUE_WORKER:
                pause()
            elif directive == SchedulerDirectiveTypes.UNPAUSE_QUEUE_WORKER:
                unpause()
    return True


@csrf_exempt
@api_safe_json_response
def directive_types(request):
    return SchedulerDirectiveTypes().all_strings_to_code()


@csrf_exempt
@api_safe_json_response
def info(request):
    result = None
    if request.method == "GET":
        result = SchedulerInfo.objects.first().to_dict()
    return result

@csrf_exempt
@api_safe_json_response
def state_types(request):
    result = None
    if request.method == "GET":
        result = SchedulerStates().all_strings_to_code()
    return result


@csrf_exempt
@api_safe_json_response
def online(request):
    result = False
    info = SchedulerInfo.get()
    if info and info.state == SchedulerStates.SCHEDULER_STATE_RUNNING:
        result = True
    return result