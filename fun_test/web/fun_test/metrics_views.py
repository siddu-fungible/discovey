import logging
import json
from dateutil.parser import parse
from django.http import HttpResponseRedirect
from django.core.management import call_command
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
from web.fun_test.metrics_models import AllocSpeedPerformanceSerializer, MetricChartSerializer, EcPerformance, \
    BcopyPerformanceSerializer
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
from lib.utilities.jira_manager import JiraManager
from lib.utilities.git_manager import GitManager
from web.fun_test.metrics_models import MetricsGlobalSettings, MetricsGlobalSettingsSerializer, MileStoneMarkers

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


@csrf_exempt
@api_safe_json_response
def describe_table(request, table_name):
    editing_chart = False
    try:
        request_json = json.loads(request.body)
        if "editing_chart" in request_json:
            editing_chart = True
    except:
        pass
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
                if editing_chart:
                    if field.column.startswith("input_") and (not field.column.startswith("input_date_time")):
                        all_values = metric_model.objects.values(field.column).distinct()
                        choices = []

                        for index, value in enumerate(all_values):
                            choices.append((index, value[field.column]))

                choices.append((len(choices), "any"))
            if hasattr(field, "verbose_name"):
                verbose_name = field.verbose_name
            payload[field.name] = {"choices": choices, "verbose_name": verbose_name}
        result = payload
    return result


@csrf_exempt
@api_safe_json_response
def chart_info(request):
    request_json = json.loads(request.body)
    metric_model_name = None
    if "metric_model_name" in request_json:
        metric_model_name = request_json["metric_model_name"]
    chart_name = None
    if "chart_name" in request_json:
        chart_name = request_json["chart_name"]
    metric_id = int(request_json["metric_id"])
    if not chart_name:
        chart = MetricChart.objects.get(metric_id=metric_id)
        milestones = MileStoneMarkers.objects.filter(metric_id=metric_id)
    else:
        chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
    result = None
    markers_dict = {}
    if chart:
        result = {"data_sets": json.loads(chart.data_sets),
                  "description": chart.description,
                  "positive": chart.positive,
                  "children": json.loads(chart.children),
                  "metric_id": chart.metric_id,
                  "chart_name": chart.chart_name,
                  "internal_chart_name": chart.internal_chart_name,
                  "metric_model_name": chart.metric_model_name,
                  "y1_axis_title": chart.y1_axis_title,
                  "y2_axis_title": chart.y2_axis_title,
                  "info": chart.description,
                  "leaf": chart.leaf,
                  "last_build_status": chart.last_build_status,
                  "last_num_degrades": chart.last_num_degrades,
                  "last_status_update_date": chart.last_status_update_date,
                  "last_num_build_failed": chart.last_num_build_failed,
                  "last_jenkins_job_id": chart.last_jenkins_job_id,
                  "last_suite_execution_id": chart.last_suite_execution_id,
                  "last_lsf_job_id": chart.last_lsf_job_id,
                  "last_git_commit": chart.last_git_commit,
                  "owner_info": chart.owner_info,
                  "source": chart.source,
                  "base_line_date": chart.base_line_date,
                  "visualization_unit": chart.visualization_unit,
                  "score_unit": chart.score_unit}
        for markers in milestones:
            markers_dict[markers.milestone_name] = markers.milestone_date
        result["milestone_markers"] = markers_dict
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
def tables(request, metric_model_name, metric_id):
    return render(request, 'qa_dashboard/analytics_tables.html', locals())


@csrf_exempt
def atomic(request, chart_name, model_name):
    return render(request, 'qa_dashboard/atomic_metric_page.html', locals())


@csrf_exempt
def score_table(request, metric_id):
    return render(request, 'qa_dashboard/score_table_page.html', locals())


@csrf_exempt
def table_view(request, model_name):
    return render(request, 'qa_dashboard/table_view_page.html', locals())


@csrf_exempt
@api_safe_json_response
def update_child_weight(request):
    request_json = json.loads(request.body)
    child_id = request_json["child_id"]
    metric_id = request_json["metric_id"]
    # lineage = request_json["lineage"]
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
    if str(child_id) in children_weights.keys():
        c.add_child_weight(child_id=child_id, weight=weight)
    invalidate_goodness_cache()
    global_settings = MetricsGlobalSettings.objects.first()
    global_settings.cache_valid = False
    global_settings.save()


'''
@csrf_exempt
def summary_page(request):
    return render(request, 'qa_dashboard/angular_home.html', locals())
'''

@csrf_exempt
def initialize(request):
    call_command('initialize')
    return HttpResponseRedirect('/')


@csrf_exempt
@api_safe_json_response
def metric_info(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    c = MetricChart.objects.get(metric_id=metric_id)
    serialized = MetricChartSerializer(c, many=False)
    serialized_data = serialized.data
    # result = c.get_status(number_of_records=6)
    result = c.get_status()

    # serialized_data["goodness_values"] = result["goodness_values"]
    # serialized_data["status_values"] = result["status_values"]
    # serialized_data["children_goodness_map"] = result["children_goodness_map"]
    # serialized_data["num_children_passed"] = result["num_children_passed"]
    # serialized_data["num_children_failed"] = result["num_children_failed"]
    # serialized_data["num_child_degrades"] = result["num_child_degrades"]
    serialized_data["children_info"] = result["children_info"]
    return serialized_data


@csrf_exempt
@api_safe_json_response
def global_settings(request):
    c = MetricsGlobalSettings.objects.first()
    serialized = MetricsGlobalSettingsSerializer(c, many=False)
    return serialized.data


@csrf_exempt
@api_safe_json_response
def scores(request):
    result = {}
    request_json = json.loads(request.body)
    metric_id = int(request_json["metric_id"])
    chart = None
    try:
        chart = MetricChart.objects.get(metric_id=metric_id)
    except:
        pass
    if chart:
        date_range = [chart.base_line_date, datetime.now()]
        entries = MetricChartStatus.objects.filter(date_time__range=date_range,
                                                   metric_id=metric_id)

    # if "date_range" in request_json:
    #     date_range = request_json["date_range"]
    #     date_range = [parser.parse(x) for x in date_range]
    #     entries = MetricChartStatus.objects.filter(date_time__range=date_range,
    #                                                metric_id=metric_id)
    # chart_name = request_json["chart_name"]
    else:
        entries = MetricChartStatus.objects.filter(metric_id=metric_id)
    serialized = MetricChartStatusSerializer(entries, many=True)
    serialized_data = serialized.data[:]
    result["scores"] = {}
    result["children_score_map"] = {}
    for element in serialized_data:
        j = dict(element)
        result["scores"][j["date_time"]] = j
        result["children_score_map"] = j["children_score_map"]

    return result


@csrf_exempt
@api_safe_json_response
def get_past_build_status(request):
    result = {}
    previous_entry = {}
    request_json = json.loads(request.body)
    metric_id = int(request_json["metric_id"])
    chart_status_entries = MetricChartStatus.objects.filter(metric_id=metric_id).order_by('-date_time')
    for entry in chart_status_entries:
        if entry.build_status == 'PASSED' or entry.copied_score is False:
            result = {"passed_jenkins_job_id": entry.jenkins_job_id,
                      "passed_suite_execution_id": entry.suite_execution_id,
                      "passed_lsf_job_id": entry.lsf_job_id,
                      "passed_date_time": entry.date_time,
                      "passed_git_commit": entry.git_commit,
                      "failed_jenkins_job_id": previous_entry.jenkins_job_id,
                      "failed_suite_execution_id": previous_entry.suite_execution_id,
                      "failed_lsf_job_id": previous_entry.lsf_job_id,
                      "failed_date_time": previous_entry.date_time,
                      "failed_git_commit": previous_entry.git_commit}
            return result
        else:
            previous_entry = entry
    result = {"failed_jenkins_job_id": previous_entry.jenkins_job_id,
              "failed_suite_execution_id": previous_entry.suite_execution_id,
              "failed_lsf_job_id": previous_entry.lsf_job_id,
              "failed_date_time": previous_entry.date_time,
              "failed_git_commit": previous_entry.git_commit}
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

def get_time_from_timestamp(timestamp):
    time_obj = parse(timestamp)
    return time_obj

@csrf_exempt
@api_safe_json_response
def update_chart(request):
    request_json = json.loads(request.body)
    model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    internal_chart_name = request_json["internal_chart_name"]

    leaf = None
    data_sets = None
    if "data_sets" in request_json:
        data_sets = request_json["data_sets"]
    description = None
    if "description" in request_json:
        description = request_json["description"]
    if "leaf" in request_json:
        leaf = request_json["leaf"]
    owner_info = "Unknown"
    if "owner_info" in request_json:
        owner_info = request_json["owner_info"]
    source = "Unknown"
    if "source" in request_json:
        source = request_json["source"]
    base_line_date = datetime(year=2018, month=4, day=1)
    if "base_line_date" in request_json:
        base_line_date = request_json["base_line_date"]
        base_line_date = get_time_from_timestamp(base_line_date)
    try:
        c = MetricChart.objects.get(metric_model_name=model_name, internal_chart_name=internal_chart_name)
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
        if owner_info:
            c.owner_info = owner_info
        if source:
            c.source = source
        if base_line_date:
            c.base_line_date = base_line_date
        if "visualization_unit" in request_json:
            visualization_unit = request_json["visualization_unit"]
            c.visualization_unit = visualization_unit
        c.save()
        global_settings = MetricsGlobalSettings.objects.first()
        global_settings.cache_valid = False
        global_settings.save()
    except ObjectDoesNotExist:
        c = MetricChart(metric_model_name=model_name,
                        chart_name=chart_name,
                        internal_chart_name=internal_chart_name,
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
            model_charts.append({"chart_name": chart.chart_name,
                                 "internal_chart_name": chart.internal_chart_name,
                                 "metric_id": chart.metric_id,
                                 "metric_model_name": chart.metric_model_name})
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
def metric_by_id(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    chart = MetricChart.objects.get(metric_id=metric_id)
    result = {}
    result["metric_model_name"] = chart.metric_model_name
    result["chart_name"] = chart.chart_name
    result["internal_chart_name"] = chart.internal_chart_name
    return result


@csrf_exempt
@api_safe_json_response
def data(request):
    request_json = json.loads(request.body)
    metric_model_name = None
    if "metric_model_name" in request_json:
        metric_model_name = request_json["metric_model_name"]
    # chart_name = request_json["chart_name"]
    metric_id = None
    if request_json["metric_id"]:
        metric_id = int(request_json["metric_id"])
    preview_data_sets = request_json["preview_data_sets"]
    chart = None
    data = []
    try:
        # chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
        if metric_id:
            chart = MetricChart.objects.get(metric_id=metric_id)
            metric_model_name = chart.metric_model_name
        model = app_config.get_metric_models()[metric_model_name]
        if preview_data_sets is not None:
            data_sets = preview_data_sets
        else:
            data_sets = chart.data_sets
            data_sets = json.loads(data_sets)
        date_range = [chart.base_line_date, datetime.now()]
        for data_set in data_sets:
            inputs = data_set["inputs"]
            d = {}
            for input_name, input_value in inputs.iteritems():
                d[input_name] = input_value
            # skip today's  #TODO
            # del d["input_date_time"]
            # today = get_current_time()
            # today = today.replace(hour=0, minute=0, second=1)
            # d["input_date_time__lt"] = today
            try:
                result = model.objects.filter(input_date_time__range=date_range, **d)  # unpack, pack
                data.append([model_to_dict(x) for x in result])
            except ObjectDoesNotExist:
                logger.critical("No data found Model: {} Inputs: {}".format(metric_model_name, str(inputs)))
    except ObjectDoesNotExist:
        logging.error("Metric Id: {} does not exist".format(metric_id))

    return data


@csrf_exempt
@api_safe_json_response
def get_data_by_model(request):
    request_json = json.loads(request.body)

    # metric_model_name = request_json["metric_model_name"]
    # chart_name = request_json["chart_name"]
    metric_id = int(request_json["metric_id"])
    preview_data_sets = request_json["preview_data_sets"]
    chart = None
    modified_data = []
    try:
        chart = MetricChart.objects.get(metric_id=metric_id)
        metric_model_name = chart.metric_model_name
        model = app_config.get_metric_models()[metric_model_name]
        if preview_data_sets is not None:
            data_sets = preview_data_sets
        else:
            data_sets = chart.data_sets
            data_sets = json.loads(data_sets)
        data = []

        d = {}
        duplicate = True
        for data_set in data_sets:
            inputs = data_set["inputs"]
            for input_name, input_value in inputs.iteritems():
                if input_name in d:
                    if d.get(input_name) != input_value:
                        duplicate = False
                d[input_name] = input_value
            # skip today's  #TODO
            # del d["input_date_time"]
            # today = get_current_time()
            # today = today.replace(hour=0, minute=0, second=1)
            # d["input_date_time__lt"] = today
            try:
                result = model.objects.filter(**d)  # unpack, pack
                data.append([model_to_dict(x) for x in result])
            except ObjectDoesNotExist:
                logger.critical("No data found Model: {} Inputs: {}".format(metric_model_name, str(inputs)))
        if duplicate is False:
            for data_set in data:
                for record in data_set:
                    modified_data.append(record)
        else:
            modified_data = data[0]
    except ObjectDoesNotExist:
        pass

    return modified_data


@csrf_exempt
def test(request):
    return render(request, 'qa_dashboard/test.html', locals())


def traverse_dag(metric_id, sort_by_name=True):
    result = {}
    chart = MetricChart.objects.get(metric_id=metric_id)

    result["metric_model_name"] = chart.metric_model_name
    result["chart_name"] = chart.chart_name
    result["children"] = json.loads(chart.children)
    result["children_info"] = {}
    result["children_weights"] = json.loads(chart.children_weights)
    result["leaf"] = chart.leaf
    result["num_leaves"] = chart.num_leaves
    result["last_num_degrades"] = chart.last_num_degrades
    result["last_num_build_failed"] = chart.last_num_build_failed
    result["positive"] = chart.positive
    result["jira_ids"] = json.loads(chart.jira_ids)

    result["copied_score"] = chart.copied_score
    result["copied_score_disposition"] = chart.copied_score_disposition
    if chart.last_good_score >= 0:
        result["last_two_scores"] = [chart.last_good_score, chart.penultimate_good_score]
    else:
        result["last_two_scores"] = [0, 0]
    if not chart.leaf or chart.chart_name == "All metrics":
        children_info = result["children_info"]
        for child_id in result["children"]:
            child_chart = MetricChart.objects.get(metric_id=child_id)
            children_info[child_chart.metric_id] = traverse_dag(metric_id=child_chart.metric_id)
        if sort_by_name:
            result["children"] = map(lambda item: item[0],
                                     sorted(children_info.iteritems(), key=lambda d: d[1]['chart_name']))
    return result


@csrf_exempt
@api_safe_json_response
def dag(request):
    result = {}
    request_json = json.loads(request.body)
    metric_model_name = request_json["metric_model_name"]
    chart_name = request_json["chart_name"]
    chart = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name)
    result[chart.metric_id] = traverse_dag(metric_id=chart.metric_id, sort_by_name=False)
    chart = MetricChart.objects.get(metric_model_name="MetricContainer", chart_name="All metrics")
    result[chart.metric_id] = traverse_dag(metric_id=chart.metric_id, sort_by_name=True)
    return result


@csrf_exempt
@api_safe_json_response
def update_jira_info(request, metric_id, jira_id):
    try:
        c = MetricChart.objects.get(metric_id=metric_id)
        if jira_id:
            jira_info = validate_jira(jira_id)
            if jira_info:
                jira_ids = json.loads(c.jira_ids)
                if jira_id not in jira_ids:
                    jira_ids.append(jira_id)
                    c.jira_ids = json.dumps(jira_ids)
                    c.save()
            else:
                raise ObjectDoesNotExist
    except ObjectDoesNotExist as obj:
        logger.critical("No data found - updating jira ids for metric id {}".format(metric_id))
        return obj.response.status_code
    return "OK"


def validate_jira(jira_id):
    project_name, id = jira_id.split('-')
    jira_obj = app_config.get_jira_manager()
    query = 'project="' + str(project_name) + '" and id="' + str(jira_id) + '"'
    try:
        jira_valid = jira_obj.get_issues_by_jql(jql=query)
        if jira_valid:
            jira_valid = jira_valid[0]
            return jira_valid
    except Exception:
        return None
    return None


@csrf_exempt
@api_safe_json_response
def delete_jira_info(request, metric_id, jira_id):
    try:
        c = MetricChart.objects.get(metric_id=metric_id)
        if jira_id:
            jira_ids = json.loads(c.jira_ids)
            if jira_id in jira_ids:
                jira_ids.remove(jira_id)
                c.jira_ids = json.dumps(jira_ids)
                c.save()
    except ObjectDoesNotExist:
        logger.critical("No data found - Deleting jira ids for metric id {}".format(metric_id))
    return "Ok"


@csrf_exempt
@api_safe_json_response
def fetch_jira_info(request, metric_id):
    jira_info = {}
    try:
        c = MetricChart.objects.get(metric_id=metric_id)
        if c.jira_ids:
            jira_ids = json.loads(c.jira_ids)
            for jira_id in jira_ids:
                jira_response = validate_jira(jira_id)
                jira_data = {}
                jira_data["id"] = jira_id
                jira_data["summary"] = jira_response.fields.summary
                jira_data["status"] = jira_response.fields.status
                jira_info[jira_id] = jira_data
    except ObjectDoesNotExist:
        logger.critical("No data found - fetching jira ids for metric id {}".format(metric_id))
    return jira_info


@csrf_exempt
@api_safe_json_response
def jiras(request, metric_id, jira_id=None):
    result = None
    if request.method == "POST":
        try:
            request_json = json.loads(request.body)
            jira_id = request_json["jira_id"]
            c = MetricChart.objects.get(metric_id=metric_id)
            if jira_id:
                jira_info = validate_jira(jira_id)
                if jira_info:
                    jira_ids = json.loads(c.jira_ids)
                    if jira_id not in jira_ids:
                        jira_ids.append(jira_id)
                        c.jira_ids = json.dumps(jira_ids)
                        c.save()
                else:
                    raise ObjectDoesNotExist
            result = "Ok"
        except ObjectDoesNotExist as obj:
            logger.critical("No data found - updating jira ids for metric Id {} jira Id: {}".format(metric_id, jira_id))
    if request.method == "GET":
        jira_info = {}
        try:
            c = MetricChart.objects.get(metric_id=metric_id)
            if c.jira_ids:
                jira_ids = json.loads(c.jira_ids)
                for jira_id in jira_ids:
                    jira_response = validate_jira(jira_id)
                    jira_data = {}
                    jira_data["id"] = jira_id
                    jira_data["summary"] = jira_response.fields.summary
                    jira_data["status"] = jira_response.fields.status
                    jira_info[jira_id] = jira_data
            result = jira_info
        except ObjectDoesNotExist:
            logger.critical("No data found - fetching jira ids for metric id {}".format(metric_id))
    if request.method == "DELETE":
        try:
            c = MetricChart.objects.get(metric_id=metric_id)
            if jira_id:
                jira_ids = json.loads(c.jira_ids)
                if jira_id in jira_ids:
                    jira_ids.remove(jira_id)
                    c.jira_ids = json.dumps(jira_ids)
                    c.save()
            result = True
        except ObjectDoesNotExist:
            logger.critical("No data found - Deleting jira ids for metric id {}".format(metric_id))
        return "Ok"
    return result


@csrf_exempt
@api_safe_json_response
def get_git_commits(request):
    result = {}
    request_json = json.loads(request.body)
    faulty_commit = request_json["faulty_commit"]
    success_commit = request_json["success_commit"]
    m = GitManager()
    commits = m.get_commits_between(faulty_commit=faulty_commit, success_commit=success_commit)
    result["commits"] = commits["commits"]
    result["changed_files"] = commits["changed_files"]
    return result
