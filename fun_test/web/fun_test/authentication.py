from django.views.decorators.csrf import csrf_exempt

from web.web_global import api_safe_json_response
import json
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist



@csrf_exempt
@api_safe_json_response
def login(request):
    result = None
    if request.method == "POST":

        request_json = json.loads(request.body)
        # username = request_json["username"]
        # password = request_json["password"]
        email = request_json["email"]
        try:
            user_object = User.objects.get(email=email)
            user = authenticate(username=user_object.username, password="fun123fun123")
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    result = True
            else:
                raise Exception("Unable to authenticate user: {}. Please contact john.abraham@fungible.com".format(email))
        except ObjectDoesNotExist:
            raise Exception("User {} does not exist. Please contact john.abraham@fungible.com".format(email))
    if request.method == "GET":
        if request.user and request.user.is_authenticated():
            result = request.user.username
    return result


@csrf_exempt
@api_safe_json_response
def logout(request):
    auth_logout(request)
    return True