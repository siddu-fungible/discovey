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
def profiles(request, id):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        first_name = request_json["first_name"]
        last_name = request_json["last_name"]
        email = request_json["email"]
        interested_metrics = request_json["interested_metrics"]

        if PerformanceUserProfile.objects.filter(email=email).count():
            raise Exception("User with email: {} already exists".format(email))
        metric_ids = interested_metrics.split(',')
        interested_metrics = {}
        for metric_id in metric_ids:
            interested_metrics[metric_id] = {"notify": False}
        new_user = PerformanceUserProfile(first_name=first_name, last_name=last_name, email=email,
                                          interested_metrics=interested_metrics)
        new_user.save()
        result = new_user.to_dict()

    elif request.method == "GET":
        users = PerformanceUserProfile.objects.all().order_by('first_name')
        user_list = []
        for user in users:
            user_list.append(user.to_dict())
        result = user_list
    elif request.method == "DELETE":
        user = PerformanceUserProfile.objects.get(id=id)
        user.delete()
    return result
