from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import User, PerformanceUserWorkspaces, LastWorkspaceId, InterestedMetrics
from django.core.exceptions import ObjectDoesNotExist
import json
from datetime import datetime


@csrf_exempt
@api_safe_json_response
def users(request, id):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        first_name = request_json["first_name"]
        last_name = request_json["last_name"]
        email = request_json["email"]

        if User.objects.filter(email=email).count():
            raise Exception("User with email: {} already exists".format(email))
        new_user = User(first_name=first_name, last_name=last_name, email=email)
        new_user.save()
        result = new_user.to_dict()
        try:
            perf_user = PerformanceUserWorkspaces.objects.get(email=email)
        except ObjectDoesNotExist:
            PerformanceUserWorkspaces(email=email).save()

    elif request.method == "GET":
        users = User.objects.all().order_by('first_name')
        user_list = []
        for user in users:
            user_list.append(user.to_dict())
        result = user_list
    elif request.method == "DELETE":
        user = User.objects.get(id=id)
        user.delete()
    return result


@csrf_exempt
@api_safe_json_response
def workspaces(request, email, workspace_name=None):
    result = []
    if request.method == "POST":
        request_json = json.loads(request.body)
        email = request_json["email"]
        name = request_json["name"]
        if "description" in request_json:
            description = request_json["description"]
        else:
            description = ""
        if "interested_metrics" in request_json:
            interested_metrics = request_json["interested_metrics"]
        else:
            interested_metrics = []
        try:
            entry = PerformanceUserWorkspaces.objects.get(email=email, workspace_name=name)
            if entry:
                entry.description = description
                entry.date_modified = datetime.now()
                entry.save()
        except ObjectDoesNotExist:
            workspace_id = LastWorkspaceId.get_next_id()
            entry = PerformanceUserWorkspaces(workspace_id=workspace_id, email=email, workspace_name=name,
                                              description=description)
            entry.save()
        result = entry.to_dict()
    elif request.method == "GET":
        if workspace_name:
            workspaces = PerformanceUserWorkspaces.objects.filter(email=email, name=workspace_name)
        else:
            workspaces = PerformanceUserWorkspaces.objects.filter(email=email)
        for workspace in workspaces:
            result.append(workspace.to_dict())
    elif request.method == "DELETE":
        workspaces = PerformanceUserWorkspaces.objects.filter(email=email)
        for workspace in workspaces:
            if workspace.name == workspace_name:
                workspace.delete()
                break
    return result

@csrf_exempt
@api_safe_json_response
def interested_metrics(request, email, workspace_id=None):
    result = []
    if request.method == "POST":
        request_json = json.loads(request.body)
        email = request_json["email"]
        workspace_id = request_json["workspace_id"]
        interested_metrics = request_json["interested_metrics"]
        metrics = interested_metrics[0]

        for metric in metrics:
            metric_id = metric
            score = metrics[metric].score
            chart_name = metrics[metric].chart_name
            subscribe = metrics[metric].subscribe
            track = metrics[metric].track
            lineage = metrics[metric].lineage
            category = metrics[metric].category
            try:
                entry = InterestedMetrics.objects.get(workspace_id= workspace_id, metric_id=metric_id)
            except ObjectDoesNotExist:
                entry = InterestedMetrics(workspace_id=workspace_id, email=email, metric_id=metric_id, score=score,
                                          chart_name=chart_name, )




