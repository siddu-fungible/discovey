from web.fun_test.django_interactive import *
from lib.utilities.send_mail import *
from web.fun_test.models import InterestedMetrics, PerformanceUserWorkspaces
from web.fun_test.metrics_models import MetricChart
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from datetime import datetime
from django.utils import timezone
from web.web_global import JINJA_TEMPLATE_DIR
from jinja2 import Environment, FileSystemLoader, Template
from fun_global import get_current_time, get_localized_time


app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
workspace_ids = [1480]
atomic_url = "http://integration.fungible.local/performance/atomic/"
negative_threshold = -5
positive_threshold = 5

def calculate_percentage(current, previous):
    percent_num = (float(current - previous) / float(previous)) * 100.0
    percentage = round(percent_num, 2)
    return percentage

def send_email(email, subject, reports):
    report_name = "performance_drop_report.html"
    file_loader = FileSystemLoader(JINJA_TEMPLATE_DIR)
    env = Environment(loader=file_loader)
    template = env.get_template(report_name)
    content = template.render(all_reports=reports)
    return send_mail(to_addresses=[email], subject=subject, content=content)

def set_dict(entries, data_set_dict):
    data_set_dict["name"] = name
    data_set_dict["today"] = getattr(entries[0], output_name)
    data_set_dict["yesterday"] = getattr(entries[1], output_name)
    data_set_dict["today_unit"] = getattr(entries[0], output_name + "_unit")
    data_set_dict["yesterday_unit"] = getattr(entries[1], output_name + "_unit")
    data_set_dict["today_date"] = str(timezone.localtime(getattr(entries[0], "input_date_time")))
    data_set_dict["yesterday_date"] = str(timezone.localtime(getattr(entries[1], "input_date_time")))

def set_percentage(data_set_dict, report, percentage):
    percentage = str(percentage) + '%'
    if "-" not in percentage:
        percentage = "+" + percentage
    data_set_dict["percentage"] = percentage
    report["data_sets"].append(data_set_dict)


if __name__ == "__main__":
    for workspace_id in workspace_ids:
        reports = []
        metrics = InterestedMetrics.objects.filter(workspace_id=workspace_id)
        email = None
        for metric in metrics:
            metric_id = metric.metric_id
            chart = MetricChart.objects.get(metric_id=metric_id)
            data_sets = json.loads(chart.data_sets)
            metric_model_name = chart.metric_model_name
            metric_model = app_config.get_metric_models()[metric_model_name]
            report = {}
            report["chart_name"] = metric.chart_name
            report["lineage"] = metric.lineage
            report["url"] = atomic_url + str(metric.metric_id)
            report["positive"] = chart.positive
            report["data_sets"] = []
            email = metric.email
            for data_set in data_sets:
                entries = metric_model.objects.filter(**data_set["inputs"]).order_by("-input_date_time")[:2]
                output_name = data_set["output"]["name"]
                name = data_set["name"]
                if len(entries) == 2:
                    data_set_dict = {}
                    set_dict(entries=entries, data_set_dict=data_set_dict)
                    if data_set_dict["today"] and data_set_dict["yesterday"]:
                        percentage = calculate_percentage(current=data_set_dict["today"], previous=data_set_dict[
                            "yesterday"])
                        if chart.positive and percentage < negative_threshold:
                            set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)
                        elif not chart.positive and percentage > positive_threshold:
                            set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)

            if len(report["data_sets"]):
                reports.append(report)
        if len(reports):
            print reports
            subject = "Performance drop report - " + str(get_current_time())
            try:
                data = send_email(email=email, subject=subject, reports=reports)
                if not data.status:
                    raise Exception("sending email failed to - {}".format(email))
                else:
                    print "sent email successfully to - {}".format(email)
            except Exception as ex:
                print str(ex)





