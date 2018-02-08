import traceback
from django.http import HttpResponse
import json
import os

PRIMARY_SETTINGS_FILE = "web.fun_test.settings"


def initialize_result(failed=False):
    status = True
    if failed:
        status = False
    return {"status": status, "error_message": "", "message": "", "data": None}


def api_safe_json_response(the_function):
    def inner(*args, **kwargs):
        result = initialize_result(failed=True)
        try:
            result["data"] = the_function(*args, **kwargs)
            result["status"] = True
        except Exception as ex:
            result["error_message"] = "Exception: {}\n {}".format(str(ex), traceback.format_exc())
        return HttpResponse(json.dumps(result))
    return inner

