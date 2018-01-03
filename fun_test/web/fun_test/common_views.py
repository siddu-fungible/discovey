from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
import logging, json
from web_global import initialize_result
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

def alerts_page(request):
    return render(request, 'qa_dashboard/alerts_page.html', locals())

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