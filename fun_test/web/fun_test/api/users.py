from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import User, PerformanceUserWorkspaces, InterestedMetrics
from django.core.exceptions import ObjectDoesNotExist
import json
from fun_global import get_current_time
from django.db.models import Q


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
        try:
            q = Q(email=email, workspace_name=name)
            entry = PerformanceUserWorkspaces.objects.get(q)
            if entry:
                entry.description = description
                entry.date_modified = get_current_time()
                entry.save()
        except ObjectDoesNotExist:
            entry = PerformanceUserWorkspaces(email=email, workspace_name=name,
                                              description=description)
            entry.save()
        result = entry.to_dict()
    elif request.method == "GET":
        if workspace_name:
            q = Q(email=email, workspace_name=workspace_name)
        else:
            q = Q(email=email)
        workspaces = PerformanceUserWorkspaces.objects.filter(q).order_by("-date_modified")
        for workspace in workspaces:
            result.append(workspace.to_dict())
    elif request.method == "DELETE":
        workspaces = PerformanceUserWorkspaces.objects.filter(email=email)
        for workspace in workspaces:
            if workspace.workspace_name == workspace_name:
                interested_metrics = InterestedMetrics.objects.filter(workspace_id=workspace.id)
                if len(interested_metrics):
                    interested_metrics.all().delete()
                workspace.delete()
                break
    return result


