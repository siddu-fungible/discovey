import logging
from django.http import HttpResponse
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from fun_global import get_datetime_from_epoch_time, get_epoch_time_from_datetime
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


@csrf_exempt
def date_test(request):
    if request.method == 'POST':
        request_json = json.loads(request.body)
        date_time = request_json["date"]
        epoch = request_json["epoch"]
        # parsed = parser.parse(date_time)
        datetime_obj = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        new_epoch = get_epoch_time_from_datetime(datetime_obj)
        print(new_epoch)
        print(epoch)
        new_datetime = get_datetime_from_epoch_time(new_epoch)
        print(new_datetime)
        print(date_time)
        checkepoch = get_epoch_time_from_datetime(new_datetime)
        print(checkepoch)
        # epochparsed = int(time.mktime(parsed.timetuple())*1000)
        return HttpResponse("OK")
    else:
        return render(request, 'qa_dashboard/datetime_conversion.html', locals())
