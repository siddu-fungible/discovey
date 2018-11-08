import traceback
from django.http import HttpResponse
import json
import os
from django.conf import settings

DB_ENGINE_TYPE_POSTGRES = "DB_ENGINE_TYPE_POSTGRES"
DB_ENGINE_TYPE_SQLITE = "DB_ENGINE_TYPE_SQLITE"

PRIMARY_SETTINGS_FILE = "web.fun_test.settings"


def initialize_result(failed=False):
    status = True
    if failed:
        status = False
    return {"status": status, "error_message": "", "message": "", "data": None}

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)

def api_safe_json_response(the_function):
    def inner(*args, **kwargs):
        result = initialize_result(failed=True)
        try:
            result["data"] = the_function(*args, **kwargs)
            result["status"] = True
        except Exception as ex:
            result["error_message"] = "Exception: {}\n {}".format(str(ex), traceback.format_exc())
        return HttpResponse(json.dumps(result, cls=DatetimeEncoder))
    return inner


def get_default_db_engine():
    result = DB_ENGINE_TYPE_SQLITE
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        result = DB_ENGINE_TYPE_POSTGRES
    return result
