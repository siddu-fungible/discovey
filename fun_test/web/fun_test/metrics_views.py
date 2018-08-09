import logging
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from fun_global import get_localized_time, get_current_time
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
from web.web_global import api_safe_json_response
from web.fun_test.site_state import site_state
from collections import OrderedDict
from web.fun_test.metrics_models import MetricChart, ModelMapping, VolumePerformanceSerializer, WuLatencyAllocStack
from web.fun_test.metrics_models import LastMetricId
from web.fun_test.metrics_models import AllocSpeedPerformanceSerializer, MetricChartSerializer, EcPerformance, BcopyPerformanceSerializer
from web.fun_test.metrics_models import BcopyFloodDmaPerformanceSerializer
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
from web.fun_test.metrics_models import LsvZipCryptoPerformance, LsvZipCryptoPerformanceSerializer
from web.fun_test.metrics_models import NuTransitPerformance, NuTransitPerformanceSerializer
from web.fun_test.metrics_models import ShaxPerformanceSerializer
from web.fun_test.metrics_models import MetricChartStatus, MetricChartStatusSerializer
from django.core import serializers, paginator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from analytics_models_helper import invalidate_goodness_cache
from datetime import datetime
from dateutil import parser
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


def index(request):
    return render(request, 'qa_dashboard/metrics.html', locals())

@csrf_exempt
@api_safe_json_response
def get_leaves(request):
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
    leaves = chart.get_leaves()
    return leaves

@api_safe_json_response
def metrics_list(request):
    return site_state.metric_models.keys()


@api_safe_json_response
def describe_table(request, table_name):
    result = None
    metric_model = app_config.get_metric_models()[table_name]
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
                  "leaf": chart.leaf,
                  "last_build_status": chart.last_build_status}
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
def table_view(request, model_name):
    return render(request, 'qa_dashboard/table_view_page.html', locals())

@csrf_exempt
@api_safe_json_response
def update_child_weight(request):
    request_json = json.loads(request.body)
    child_id = request_json["child_id"]
    metric_id = request_json["metric_id"]
    lineage = request_json["lineage"]
    weight = request_json["weight"]
    '''
    Enable it later
    c = None
    while lineage:
        lineage_metric_id = lineage.pop()
        c = MetricChart.objects.get(metric_id=lineage_metric_id)
    '''
    c = MetricChart.objects.get(metric_id=metric_id)
    children_weights = c.get_children_weights()
    if child_id in children_weights:
        c.add_child_weight(child_id=child_id, weight=weight)
    invalidate_goodness_cache()

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
    result = c.get_status(number_of_records=6)
    serialized_data["goodness_values"] = result["goodness_values"]
    serialized_data["status_values"] = result["status_values"]
    serialized_data["children_goodness_map"] = result["children_goodness_map"]
    serialized_data["num_children_passed"] = result["num_children_passed"]
    serialized_data["num_children_failed"] = result["num_children_failed"]
    serialized_data["num_child_degrades"] = result["num_child_degrades"]
    serialized_data["children_info"] = result["children_info"]
    return serialized_data



@csrf_exempt
@api_safe_json_response
def scores(request):
    result = {}
    request_json = json.loads(request.body)
    date_range = request_json["date_range"]
    date_range = [parser.parse(x) for x in date_range]
    # chart_name = request_json["chart_name"]
    metric_id = int(request_json["metric_id"])
    entries = MetricChartStatus.objects.filter(date_time__range=date_range,
                                               metric_id=metric_id)
    serialized = MetricChartStatusSerializer(entries, many=True)
    serialized_data = serialized.data[:]
    result["scores"] = {}
    for element in serialized_data:
        j = dict(element)
        result["scores"][j["date_time"]] = j

    return result

@csrf_exempt
@api_safe_json_response
def table_data(request, page=None, records_per_page=10):
    request_json = json.loads(request.body)
    model_name = request_json["model_name"]
    model = app_config.get_metric_models()[model_name]
    data = {}
    header_list = [x.name for x in model._meta.get_fields()]
    data["headers"] = header_list
    data["data"] = {}
    data["fields"] = OrderedDict()
    data["total"] = 0
    fields = data["fields"]
    for field in model._meta.get_fields():
        choices = None
        if hasattr(field, "choices"):
            choices = field.choices
        if hasattr(field, "verbose_name"):
            verbose_name = field.verbose_name
            fields[field.name] = {"choices": choices, "verbose_name": verbose_name}
    serializer_map = {"VolumePerformance": VolumePerformanceSerializer,
                      "AllocSpeedPerformance": AllocSpeedPerformanceSerializer,
                      "WuLatencyAllocStack": WuLatencyAllocStack,
                      "EcPerformance": EcPerformance,
                      "BcopyPerformance": BcopyPerformanceSerializer,
                      "BcopyFloodDmaPerformance": BcopyFloodDmaPerformanceSerializer,
                      "JenkinsJobIdMap": JenkinsJobIdMapSerializer,
                      "LsvZipCryptoPerformance": LsvZipCryptoPerformanceSerializer,
                      "NuTransitPerformance": NuTransitPerformanceSerializer,
                      "ShaxPerformance": ShaxPerformanceSerializer}
    serializer = serializer_map[model_name]
    all_entries = model.objects.all().order_by()
    if hasattr(model.objects.first(), "input_date_time"):
        all_entries = all_entries.order_by("-input_date_time")
    else:
        all_entries = all_entries.order_by("-id")

    data["total_count"] = all_entries.count()
    if page:
        p = paginator.Paginator(all_entries, records_per_page)
        all_entries = p.page(page)

    s = serializer(all_entries, many=True)
    data["data"] = s.data
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
        if leaf:
            c.leaf = leaf
        c.save()
        invalidate_goodness_cache()
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
        data["status"], data["goodness"] = status["status_values"][-1], status["goodness_values"][-1]
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
    model = app_config.get_metric_models()[metric_model_name]
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
        # skip today's  #TODO
        # del d["input_date_time"]
        today = get_current_time()
        today = today.replace(hour=0, minute=0, second=1)
        d["input_date_time__lt"] = today
        try:
            result = model.objects.filter(**d)   #unpack, pack


            data.append([model_to_dict(x) for x in result])
        except ObjectDoesNotExist:
            logger.critical("No data found Model: {} Inputs: {}".format(metric_model_name, str(inputs)))
    return data


@csrf_exempt
def test(request):
    return render(request, 'qa_dashboard/test.html', locals())
