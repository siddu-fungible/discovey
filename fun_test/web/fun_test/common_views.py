from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
import logging, json
from web.web_global import api_safe_json_response, initialize_result
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic
from web.fun_test.models import TimeKeeper

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

def alerts_page(request):
    return render(request, 'qa_dashboard/alerts_page.html', locals())

def home(request):
    request.session.clear()
    return render(request, 'qa_dashboard/home.html', locals())

@csrf_exempt
def add_session_log(request):
    if not "logs" in request.session:
        request.session["logs"] = []
    request_json = json.loads(request.body)
    log = request_json
    request.session["logs"].append(log)
    request.session.save()
    return HttpResponse("Ok")

def get_session_logs(request):
    logs = []
    if "logs" in request.session:
        logs = request.session["logs"]
    logs.reverse()
    return HttpResponse(json.dumps(logs))

@csrf_exempt
@api_safe_json_response
def time_keeper(request, name):
    return TimeKeeper.get(name=name)