from web.fun_test.metrics_models import *
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.send_mail import *
from jinja2 import Environment, FileSystemLoader, Template
from web.fun_test.models import InterestedMetrics
from django.db.models import Q
from web.web_global import JINJA_TEMPLATE_DIR
from web.fun_test.metrics_lib import MetricLib

ml = MetricLib()


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
def metrics_data(request):
    data = []
    if request.method == "GET":
        metric_id = request.GET.get("metric_id", None)
        from_epoch_ms = request.GET.get("from_epoch_ms", None)
        to_epoch_ms = request.GET.get("to_epoch_ms", None)
        order_by = request.GET.get("order_by", None)
        count = int(request.GET.get("count", 1))
        if metric_id:
            chart = MetricChart.objects.get(metric_id=metric_id)
            model = app_config.get_metric_models()[chart.metric_model_name]
            data_sets = json.loads(chart.data_sets)
            q = None
            if from_epoch_ms and to_epoch_ms:
                from_epoch = float(int(from_epoch_ms) / 1000)
                to_epoch = float(int(to_epoch_ms) / 1000)
                to_time = datetime.fromtimestamp(to_epoch)
                from_time = datetime.fromtimestamp(from_epoch)
                date_range = [from_time, to_time]
                q = Q(input_date_time__range=date_range)
                order_by = "-input_date_time"
            for data_set in data_sets:
                inputs = data_set["inputs"]
                d = {}
                for input_name, input_value in inputs.iteritems():
                    d[input_name] = input_value
                if q:
                    new_q = q & Q(**d)
                else:
                    new_q = Q(**d)
                results = model.objects.filter(new_q).order_by(order_by)[:count]
                if len(results):
                    for result in results:
                        output_name = data_set["output"]["name"]
                        date_time = getattr(result, "input_date_time")
                        value = getattr(result, output_name)
                        unit = getattr(result, output_name + "_unit")
                        temp = {"name": data_set["name"], "value": value, "unit": unit, "date_time": date_time}
                        data.append(temp)
    elif request.method == "POST":
        request_json = json.loads(request.body)
        reports = request_json["reports"]
        email = request_json["email"]
        subject = request_json["subject"]
        # print reports
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

        # total entries in interested metrics and deleting the ones which are not tracked
        interested_entries = InterestedMetrics.objects.filter(workspace_id=workspace_id)
        if len(interested_entries):
            for entry in interested_entries:
                delete = False
                for metric in interested_metrics:
                    metric_id = metric["metric_id"]
                    if entry.metric_id == metric["metric_id"]:
                        delete = False
                        break
                    else:
                        delete = True
                if delete:
                    entry.delete()

        for metric in interested_metrics:
            metric_id = metric["metric_id"]
            chart_name = metric["chart_name"]
            subscribe = metric["subscribe"]
            track = metric["track"]
            lineage = metric["lineage"]
            category = metric["category"]
            comments = metric["comments"]
            try:
                q = Q(workspace_id=workspace_id, metric_id=metric_id)
                entry = InterestedMetrics.objects.get(q)
                entry.subscribe = subscribe
                entry.track = track
                entry.category = category
                entry.lineage = lineage
                entry.comments = comments
                entry.save()
                result.append(entry.to_dict())
            except ObjectDoesNotExist:
                entry = InterestedMetrics(workspace_id=workspace_id, email=email, metric_id=metric_id,
                                          chart_name=chart_name, subscribe=subscribe, track=track, category=category,
                                          lineage=lineage, comments=comments)
                entry.save()
                result.append(entry.to_dict())
    elif request.method == "GET":
        q = Q(workspace_id=workspace_id)
        interested_metrics = InterestedMetrics.objects.filter(q)
        for metric in interested_metrics:
            metric = metric.to_dict()
            _set_interested_metrics(metric=metric)
            result.append(metric)
    elif request.method == "DELETE":
        metric_id = request.GET.get("metric_id", None)
        if metric_id:
            q = Q(workspace_id=workspace_id, metric_id=metric_id)
            entry = InterestedMetrics.objects.get(q)
            entry.delete()
    return result


def _set_interested_metrics(metric):
    metric_id = metric["metric_id"]
    metric["children"] = []
    mc = MetricChart.objects.get(metric_id=metric_id)
    if not mc.leaf:
        children = mc.get_children()
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=int(child))
            new_metric = {}
            new_metric["workspace_id"] = metric["workspace_id"]
            new_metric["email"] = metric["email"]
            new_metric["metric_id"] = int(child)
            new_metric["subscribe"] = metric["subscribe"]
            new_metric["track"] = metric["track"]
            new_metric["chart_name"] = child_chart.chart_name
            new_metric["category"] = metric["category"]
            new_metric["lineage"] = metric["lineage"] + "/" + child_chart.chart_name
            new_metric["date_created"] = metric["date_created"]
            new_metric["date_modified"] = metric["date_modified"]
            new_metric["comments"] = metric["comments"]
            _set_interested_metrics(metric=new_metric)
            metric["children"].append(new_metric)


@csrf_exempt
@api_safe_json_response
def metric_charts(request, metric_id=None):
    result = []
    if request.method == "GET":
        workspace_id = request.GET.get("workspace_id", None)
        q = Q()
        if workspace_id:
            q = Q(workspace_ids__contains=int(workspace_id))
        if metric_id:
            q = Q(metric_id=metric_id)
        charts = MetricChart.objects.filter(q)
        for chart in charts:
            chart_dict = {}
            chart_dict["metric_id"] = chart.metric_id
            result.append(chart_dict)
    return result


@csrf_exempt
@api_safe_json_response
def attach_to_dag(request):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        attach_id = int(request_json["attach_id"])
        original_metric_id = int(request_json["original_metric_id"])
        try:
            mc = MetricChart.objects.get(metric_id=original_metric_id)
            ml.set_global_cache(False)
            mc.add_child(child_id=attach_id)
            mc.fix_children_weights()
            result = mc.to_dict()
        except:
            pass
    elif request.method == "DELETE":
        attached_id = request.GET.get("attached_metric_id", None)
        original_metric_id = request.GET.get("original_metric_id", None)
        if attached_id and original_metric_id:
            try:
                mc = MetricChart.objects.get(metric_id=int(original_metric_id))
                ml.set_global_cache(False)
                mc.remove_child(child_id=int(attached_id))
                mc.fix_children_weights()
                result = mc.to_dict()
            except:
                pass
    return result
