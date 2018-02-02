import logging
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from web.web_global import initialize_result, api_safe_json_response
from web.fun_test.site_state import site_state

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)


def index(request):
    return render(request, 'qa_dashboard/metrics.html', locals())


@api_safe_json_response
def metrics_list(request):
    metric_names = [x.__name__ for x in site_state.metric_models]
    return metric_names
