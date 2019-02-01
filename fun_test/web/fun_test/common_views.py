from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
import logging, json
from web.web_global import api_safe_json_response, initialize_result
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic
from web.fun_test.models import TimeKeeper
from web.fun_test.metrics_views import validate_jira

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

@csrf_exempt
@api_safe_json_response
def bug_info(request):
    result = None
    if request.method == "POST":
        jira_info = {}
        try:
            request_json = json.loads(request.body)
            bug_ids = request_json["bug_ids"]
            for jira_id in bug_ids:
                jira_response = validate_jira(jira_id)
                jira_data = {}
                jira_data["id"] = jira_id
                jira_data["summary"] = jira_response.fields.summary
                jira_data["status"] = jira_response.fields.status
                jira_info[jira_id] = jira_data
            result = jira_info
        except ObjectDoesNotExist as obj:
            logger.critical("No data found")
    return result