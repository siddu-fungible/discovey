import logging
import json
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from web.web_global import api_safe_json_response
from web.fun_test.site_state import site_state
from collections import OrderedDict
from web.fun_test.metrics_models import MetricChart, ModelMapping, ANALYTICS_MAP, VolumePerformanceSerializer
from web.fun_test.metrics_models import LastMetricId
from web.fun_test.metrics_models import AllocSpeedPerformanceSerializer, MetricChartSerializer
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
    metric_model = ANALYTICS_MAP[table_name]["model"]
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
        result = {"data_sets": json.loads(chart.data_sets),
                  "description": chart.description,
                  "positive": chart.positive,
                  "children": json.loads(chart.children),
                  "metric_id": chart.metric_id,
                  "y1_axis_title": chart.y1_axis_title,
                  "y2_axis_title": chart.y2_axis_title,
                  "info": chart.description,
                  "leaf": chart.leaf}
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
def view_all_storage_charts(request):
    return render(request, 'qa_dashboard/analytics_chart_dashboard.html', locals())


@csrf_exempt
def view_all_system_charts(request):
    return render(request, 'qa_dashboard/system_charts.html', locals())


@csrf_exempt
def tables(request, metric_model_name, chart_name):
    return render(request, 'qa_dashboard/analytics_tables.html', locals())

@csrf_exempt
def atomic(request, chart_name, model_name):
    return render(request, 'qa_dashboard/atomic_metric_page.html', locals())


@csrf_exempt
def summary_page(request):
    return render(request, 'qa_dashboard/metrics_summary.html', locals())

@csrf_exempt
@api_safe_json_response
def metric_info(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    c = MetricChart.objects.get(metric_id=metric_id)
    serialized = MetricChartSerializer(c, many=False)
    serialized_data = serialized.data
    status_values, goodness_values = c.get_status(number_of_records=5)
    serialized_data["goodness_values"] = goodness_values
    serialized_data["status_values"] = status_values
    return serialized_data

@csrf_exempt
@api_safe_json_response
def table_data(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    model = ANALYTICS_MAP[metric_model_name]["model"]
    key = "key"
    unique_keys = model.objects.values(key).distinct()
    unique_keys = [x[key] for x in unique_keys]
    data = {}
    header_list = [x.name for x in model._meta.get_fields()]
    data["headers"] = header_list
    data["data"] = {}
    '''
    the_data = data["data"]
    for unique_key in unique_keys:
        entries = model.objects.filter(key=unique_key)
        the_data[unique_key] = []
        for entry in entries:
            row = []
            for header in header_list:
                row.append(getattr(entry, header))
            the_data[unique_key].append(row)
    '''
    serializer_map = {"VolumePerformance": VolumePerformanceSerializer,
                      "AllocSpeedPerformance": AllocSpeedPerformanceSerializer}
    serializer = serializer_map[metric_model_name]
    all_entries = model.objects.all()
    s = serializer(all_entries, many=True)
    data["data"] = s.data
    data["unique_keys"] = unique_keys
    return data

@csrf_exempt
@api_safe_json_response
def update_chart(request):
    request_json = json.loads(request.body)
    model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]

    leaf = None
    data_sets = None
    if "data_sets" in request_json:
        data_sets = request_json["data_sets"]
    description = None
    if "description" in request_json:
        description = request_json["description"]
    if "leaf" in request_json:
        leaf = request_json["leaf"]

    try:
        c = MetricChart.objects.get(metric_model_name=model_name, chart_name=chart_name)
        if data_sets:
            c.data_sets = json.dumps(data_sets)
        if description:
            c.description = description
        if "negative_gradient" in request_json:
            c.positive = not request_json["negative_gradient"]
        if "y1_axis_title" in request_json:
            c.y1axis_title = request_json["y1_axis_title"] if request_json["y1_axis_title"] else ""
        if "y2_axis_title" in request_json:
            c.y2axis_title = request_json["y2_axis_title"] if request_json["y2_axis_title"] else ""
        if leaf:
            c.leaf = leaf
        c.save()
    except ObjectDoesNotExist:
        c = MetricChart(metric_model_name=model_name,
                        chart_name=chart_name,
                        data_sets=json.dumps(data_sets),
                        metric_id=LastMetricId.get_next_id())
        c.save()
    return "Ok"


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
def status(request):
    data = {"status": False, "goodness": 0}
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    try:
        chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
        status = chart.get_status()
        data["status"], data["goodness"] = status[0][-1], status[1][-1]
    except ObjectDoesNotExist:
        pass
    return data

@csrf_exempt
@api_safe_json_response
def data(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    preview_data_sets = request_json["preview_data_sets"]
    chart = None
    try:
        chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
    except ObjectDoesNotExist:
        pass
    model = ANALYTICS_MAP[metric_model_name]["model"]
    if preview_data_sets is not None:
        data_sets = preview_data_sets
    else:
        data_sets = chart.data_sets
        data_sets = json.loads(data_sets)
    data = []
    for data_set in data_sets:
        inputs = data_set["inputs"]
        d = {}
        for input_name, input_value in inputs.iteritems():
            d[input_name] = input_value
        try:
            result = model.objects.filter(**d)   #unpack, pack
            data.append([model_to_dict(x) for x in result])
        except ObjectDoesNotExist:
            logger.critical("No data found Model: {} Inputs: {}".format(metric_model_name, str(inputs)))
    return data
