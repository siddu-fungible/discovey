from web.fun_test.metrics_models import *
from django.views.decorators.csrf import csrf_exempt


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
def companion_chart_info(request):
    result = {}
    if request.method == "POST":
        request_json = json.loads(request.body)
        id = request_json["chart_id"]
        try:
            chart = Chart.objects.get(chart_id=id)
            if chart:
                result["yaxis_title"] = chart.yaxis_title
                result["xaxis_title"] = chart.xaxis_title
                result["data_sets"] = chart.data_sets
                result["title"] = chart.title
        except ObjectDoesNotExist:
            result = {}
    return result


@csrf_exempt
@api_safe_json_response
def get_data_sets_value(request):
    result = {}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    if request.method == "POST":
        request_json = json.loads(request.body)
        companion_chart_info = request_json["companion_chart_info"]
        data_sets = companion_chart_info["data_sets"]
        for data_set in data_sets:
            data_set_name = data_set["name"]
            result[data_set_name] = {}
            inputs = data_set["inputs"]
            output = data_set["output"]["name"]
            data_set_dict = {}
            data_set_dict["unit"] = None
            data_set_dict["values"] = []
            for input in inputs:
                xvalue = input["name"]
                model_name = input["model_name"]
                metric_model = app_config.get_metric_models()[model_name]
                date_range = [datetime.now() - timedelta(days=10), datetime.now()]
                entries = metric_model.objects.filter(input_date_time__range=date_range,
                                                      **input["filter"]).order_by('-input_date_time')
                if entries:
                    entry = entries[0]
                    if hasattr(entry, output):
                        output_value = getattr(entry, output)
                        unit_name = output + "_unit"
                        output_unit = getattr(entry, unit_name)
                        data_set_dict["unit"] = output_unit
                        data_set_dict["values"].append({"x": xvalue, "y": output_value})
                    else:
                        data_set_dict["values"].append({"x": xvalue, "y": None})
                else:
                    data_set_dict["values"].append({"x": xvalue, "y": None})
            result[data_set_name] = data_set_dict
    return result
