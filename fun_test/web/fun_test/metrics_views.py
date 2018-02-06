import logging
import json
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from web.web_global import api_safe_json_response
from web.fun_test.site_state import site_state
from collections import OrderedDict
from web.fun_test.metrics_models import MetricChart, ModelMapping
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)


def index(request):
    return render(request, 'qa_dashboard/metrics.html', locals())


@api_safe_json_response
def metrics_list(request):
    return site_state.metric_models.keys()


@api_safe_json_response
def describe_table(request, table_name):
    result = None
    metric_model = site_state.get_metric_model_by_name(name=table_name)
    if metric_model:
        fields = metric_model._meta.get_fields()
        payload = OrderedDict()
        for field in fields:
            choices = None
            verbose_name = "verbose_name"
            if hasattr(field, "choices"):
                choices = field.choices
            if hasattr(field, "verbose_name"):
                verbose_name = field.verbose_name
            payload[field.name] = {"choices": choices, "verbose_name": verbose_name}
        result = payload
    return result


@csrf_exempt
@api_safe_json_response
def chart_info(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
    result = None
    if chart:
        result = {"data_sets": json.loads(chart.data_sets)}
    return result


@csrf_exempt
@api_safe_json_response
def charts_info(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    charts = MetricChart.objects.filter(metric_model_name=metric_model_name)
    result = OrderedDict()
    for chart in charts:
        result[chart.chart_name] = {"data_sets": json.loads(chart.data_sets)}
    return result


@csrf_exempt
@api_safe_json_response
def chart_list(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    charts = MetricChart.objects.filter(metric_model_name=metric_model_name)
    return [chart.chart_name for chart in charts]


@csrf_exempt
@api_safe_json_response
def charts_by_module(request):
    request_json = json.loads(request.body)
    module_name = request_json["module_name"]
    entries = ModelMapping.objects.filter(module=module_name)
    models = []
    for entry in entries:
        models.append(entry.model_name)
    result = []
    for model in models:
        charts = MetricChart.objects.filter(metric_model_name=model)
        for chart in charts:
            result.append({"chart_name": chart.chart_name, "model": model})
    return result


@csrf_exempt
def edit_chart(request, chart_name):
    return render(request, 'qa_dashboard/edit_chart.html', locals())

@csrf_exempt
@api_safe_json_response
def models_by_module(request):
    request_json = json.loads(request.body)
    module_name = request_json["module_name"]
    entries = ModelMapping.objects.filter(module=module_name)
    models = []
    for entry in entries:
        models.append(entry.model_name)
    result = {}

    for model in models:
        charts = MetricChart.objects.filter(metric_model_name=model)
        model_charts = []
        result[model] = {"charts": model_charts}
        for chart in charts:
            model_charts.append(chart.chart_name)
    return result


@csrf_exempt
@api_safe_json_response
def data(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)

    model = site_state.get_metric_model_by_name(name=metric_model_name)
    data_sets = chart.data_sets
    data_sets = json.loads(data_sets)
    data = []
    for data_set in data_sets:
        inputs = data_set["inputs"]
        d = {}
        for input_name, input_value in inputs.iteritems():
            d[input_name] = input_value
        try:
            result = model.objects.filter(**d)
            data.append([model_to_dict(x) for x in result])
        except ObjectDoesNotExist:
            logger.critical("No data found Model: {} Inputs: {}".format(metric_model_name, str(inputs)))
    return data
