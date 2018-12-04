import logging
from django.http import HttpResponse
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


@csrf_exempt
def home(request):
    return render(request, 'qa_dashboard/angular_home.html', locals())
