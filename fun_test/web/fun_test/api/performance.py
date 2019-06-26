from web.fun_test.metrics_models import *
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.db_fixup import convert_to_base_unit
import math

@csrf_exempt
@api_safe_json_response
def charts(request, id):
    result = None
    if request.method == "GET":
        if id:
            chart = MetricChart.objects.get(metric_id=id)
            milestones = MileStoneMarkers.objects.filter(metric_id=id)
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
                          "pk": chart.pk,
                          "companion_charts": chart.companion_charts}
                if milestones:
                    markers_dict = {}
                    for markers in milestones:
                        markers_dict[markers.milestone_name] = markers.milestone_date
                    result["milestone_markers"] = markers_dict
    return result


@csrf_exempt
@api_safe_json_response
def companion_charts(request):
    result = {}
    if request.method == "POST":
        request_json = json.loads(request.body)
        ids = request_json["chart_ids"]
        for id in ids:
            one_chart_info = {}
            try:
                chart = Chart.objects.get(chart_id=id)
                if chart:
                    one_chart_info = {}
                    one_chart_info["yaxis_title"] = chart.yaxis_title
                    one_chart_info["xaxis_title"] = chart.xaxis_title
                    one_chart_info["data_sets"] = chart.data_sets
                    one_chart_info["data_set_names"] = chart.data_sets["names"]
                result[id] = one_chart_info
            except ObjectDoesNotExist:
                result[id] = one_chart_info
    return result


@csrf_exempt
@api_safe_json_response
def get_data_sets_value(request):
    result = {}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    if request.method == "POST":
        request_json = json.loads(request.body)
        companion_charts = request_json["companion_charts"]
        metric_id = int(request_json["metric_id"])
        if metric_id:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                children = json.loads(chart.children)
                for companion_chart in companion_charts:
                    result[companion_chart] = {}
                    data_sets = companion_charts[companion_chart]["data_sets"]["names"]
                    for child in children:
                        child_chart = MetricChart.objects.get(metric_id=child)
                        result[companion_chart][child_chart.chart_name] = []
                        chart_data_sets = json.loads(child_chart.data_sets)
                        metric_model = app_config.get_metric_models()[child_chart.metric_model_name]
                        for data_set in chart_data_sets:
                            if data_set["name"] in data_sets:
                                data_set_dict = {}
                                output_value = -1
                                output_unit = ""
                                date_range = [datetime.now() - timedelta(days=2), datetime.now()]
                                entries = metric_model.objects.filter(**data_set[
                                    "inputs"]).order_by('-input_date_time')
                                if entries:
                                    entry = entries[0]
                                    output_name = data_set["output"]["name"]
                                    if hasattr(entry, output_name):
                                        output_value = getattr(entry, output_name)
                                        unit_name = output_name + "_unit"
                                        output_unit = getattr(entry, unit_name)
                                        output_value = convert_to_base_unit(output_value=output_value,
                                                                            output_unit=output_unit)
                                        output_value = math.log10(output_value)
                                        data_set_dict["name"] = data_set["name"]
                                        data_set_dict["value"] = output_value
                                        data_set_dict["unit"] = output_unit
                                        result[companion_chart][child_chart.chart_name].append(data_set_dict)
                                else:
                                    data_set_dict["name"] = data_set["name"]
                                    data_set_dict["value"] = None
                                    data_set_dict["unit"] = ""
                                    result[companion_chart][child_chart.chart_name].append(data_set_dict)
    return result
