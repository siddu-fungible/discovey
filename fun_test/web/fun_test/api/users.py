from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import User, PerformanceUserProfile
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
        PerformanceUserProfile(email=email).save()

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
def profile(request, id):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        email = request_json["email"]
        workspace = None
        if "workspace" in request_json:
            workspace = request_json["workspace"]

        profile = PerformanceUserProfile.objects.get(email=email)
        match_found = False
        if workspace:
            for ws in profile.workspace:
                if ws["name"] == workspace["name"]:
                    match_found = True
            if not match_found:
                profile.workspace.append(workspace)
                profile.save()
            else:
                for ws in profile.workspace:
                    if ws["name"] == workspace["name"]:
                        ws["interested_metrics"] = workspace["interested_metrics"]
                profile.save()
        result = profile.to_dict()

    elif request.method == "GET":
        profile = PerformanceUserProfile.objects.get(email=id)
        result = profile.to_dict()
    elif request.method == "DELETE":
        profile = PerformanceUserProfile.objects.get(id=id)
        profile.delete()
    return result


@csrf_exempt
@api_safe_json_response
def edit_profile(request, id):
    result = None

