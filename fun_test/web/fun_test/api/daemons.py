from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import Daemon
from django.db.models import Q


def fun_model_api_handler(request, model, id=None):
    result = None
    if request.method == "GET":
        q = Q()
        model_objects = model.objects.filter(q)
        result = map(lambda x: x.to_dict(), model_objects)
    return result


@csrf_exempt
@api_safe_json_response
def daemons(request, id):
    return fun_model_api_handler(request=request, model=Daemon, id=id)