from web.fun_test.metrics_models import *
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.send_mail import *
from jinja2 import Environment, FileSystemLoader, Template
from web.fun_test.models import InterestedMetrics
from django.db.models import Q
from web.web_global import JINJA_TEMPLATE_DIR

@csrf_exempt
@api_safe_json_response
def charts(request, id):
    result = {}
    if request.method == "GET":
        try:
            chart = Chart.objects.get(chart_id=id)
            if chart:
                result["y_axis_title"] = chart.y_axis_title
                result["x_axis_title"] = chart.x_axis_title
                result["series_filters"] = chart.series_filters
                result["title"] = chart.title
                result["chart_type"] = chart.chart_type
                result["fun_chart_type"] = chart.fun_chart_type
                result["x_scale"] = chart.x_scale
                result["y_scale"] = chart.y_scale
        except ObjectDoesNotExist:
            result = {}
    return result


@csrf_exempt
@api_safe_json_response
def data(request):
    result = {}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    if request.method == "POST":
        request_json = json.loads(request.body)
        chart = request_json["chart_info"]
        series_filters = chart["series_filters"]
        for filter in series_filters:
            filter_name = filter["name"]
            result[filter_name] = {}
            inputs = filter["filters"]
            output = filter["output_field"]
            data_set_dict = {}
            data_set_dict["unit"] = None
            data_set_dict["values"] = []
            for input in inputs:
                xvalue = input["name"]
                model_name = input["model_name"]
                metric_model = app_config.get_metric_models()[model_name]
                entries = metric_model.objects.filter(**input["filter"]).order_by('-input_date_time')
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
            result[filter_name] = data_set_dict
    return result

@csrf_exempt
@api_safe_json_response
def report_data(request):
    data = []
    if request.method == "GET":
        metric_id = request.GET.get("metric_id", None)
        from_epoch_ms = int(request.GET.get("from_epoch_ms", None))
        to_epoch_ms = int(request.GET.get("to_epoch_ms", None))
        if metric_id and from_epoch_ms and to_epoch_ms:
            chart = MetricChart.objects.get(metric_id=metric_id)
            model = app_config.get_metric_models()[chart.metric_model_name]
            from_epoch = float(from_epoch_ms / 1000)
            to_epoch = float(to_epoch_ms / 1000)
            to_time = datetime.fromtimestamp(to_epoch)
            from_time = datetime.fromtimestamp(from_epoch)
            date_range = [from_time, to_time]
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                inputs = data_set["inputs"]
                d = {}
                for input_name, input_value in inputs.iteritems():
                    d[input_name] = input_value
                results = model.objects.filter(input_date_time__range=date_range, **d).order_by(
                    "-input_date_time")
                if len(results):
                    result = results[0]
                    output_name = data_set["output"]["name"]
                    value = getattr(result, output_name)
                    unit = getattr(result, output_name + "_unit")
                    temp = {"name": data_set["name"], "value": value, "unit": unit}
                    data.append(temp)
    elif request.method == "POST":
        request_json = json.loads(request.body)
        reports = request_json["reports"]
        email = request_json["email"]
        subject = request_json["subject"]
        file_loader = FileSystemLoader(JINJA_TEMPLATE_DIR)
        env = Environment(loader=file_loader)
        template = env.get_template('performance_report.html')
        content = template.render(all_reports=reports)
        data = send_mail(to_addresses=[email], subject=subject, content=content)
    return data

@csrf_exempt
@api_safe_json_response
def interested_metrics(request, workspace_id=None):
    result = []
    if request.method == "POST":
        request_json = json.loads(request.body)
        email = request_json["email"]
        workspace_id = request_json["workspace_id"]
        interested_metrics = request_json["interested_metrics"]

        for metric in interested_metrics:
            metric_id = metric["metric_id"]
            chart_name = metric["chart_name"]
            subscribe = metric["subscribe"]
            track = metric["track"]
            lineage = metric["lineage"]
            category = metric["category"]
            try:
                q = Q(workspace_id=workspace_id, metric_id=metric_id)
                entry = InterestedMetrics.objects.get(q)
                entry.subscribe = subscribe
                entry.track = track
                entry.category = category
                entry.lineage = lineage
                entry.save()
                result.append(entry.to_dict())
            except ObjectDoesNotExist:
                entry = InterestedMetrics(workspace_id=workspace_id, email=email, metric_id=metric_id,
                                          chart_name=chart_name, subscribe=subscribe, track=track, category=category,
                                          lineage=lineage)
                entry.save()
                result.append(entry.to_dict())
    elif request.method == "GET":
        q = Q(workspace_id=workspace_id)
        interested_metrics = InterestedMetrics.objects.filter(q)
        for metric in interested_metrics:
            result.append(metric.to_dict())
    elif request.method == "DELETE":
        metric_id = request.GET.get("metric_id", None)
        if metric_id:
            q = Q(workspace_id=workspace_id, metric_id=metric_id)
            entry = InterestedMetrics.objects.get(q)
            entry.delete()
    return result
