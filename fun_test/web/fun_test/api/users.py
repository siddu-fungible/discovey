from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import User, PerformanceUserWorkspaces
from django.core.exceptions import ObjectDoesNotExist
import json


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
        description = request_json["description"]
        try:
            entry = PerformanceUserWorkspaces.objects.get(email=email, name=name)
            if entry:
                entry.description = description
                entry.save()
        except ObjectDoesNotExist:
            entry = PerformanceUserWorkspaces(email=email, name=name, description=description).save()
        result = entry.to_dict()
    elif request.method == "GET":
        workspaces = PerformanceUserWorkspaces.objects.filter(email=email)
        for workspace in workspaces:
            result.append(workspace.to_dict())
    elif request.method == "DELETE":
        profile = PerformanceUserWorkspaces.objects.get(email=email)
        for ws in profile.workspace:
            if ws["name"] == workspace_name:
                profile.workspace.remove(ws)
        profile.save()
    return result


@csrf_exempt
@api_safe_json_response
def edit_workspace(request, email):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        workspace_name = request_json["workspace_name"]
        interested_metrics = request_json["interested_metrics"]
        description = request_json["description"]
        profile = PerformanceUserWorkspaces.objects.get(email=email)
        for ws in profile.workspace:
            if ws["name"] == workspace_name:
                ws["interested_metrics"] = interested_metrics
                ws["description"] = description
        profile.save()
        result = profile.to_dict()
    return result
