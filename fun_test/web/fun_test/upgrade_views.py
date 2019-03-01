import logging
from django.http import HttpResponse
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from fun_global import is_triaging_mode, is_production_mode
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


@csrf_exempt
def home(request):
    angular_home = 'qa_dashboard/angular_home_development.html'
    if is_production_mode() and not is_triaging_mode():
        angular_home = 'qa_dashboard/angular_home_production.html'
    return render(request, angular_home, locals())
