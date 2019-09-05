from lib.system.fun_test import *
from web.fun_test.django_interactive import *
from lib.utilities.send_mail import *
from web.fun_test.models import InterestedMetrics
from web.fun_test.metrics_models import MetricChart
import json
from django.apps import apps
from fun_settings import MAIN_WEB_APP
from django.utils import timezone
from web.web_global import JINJA_TEMPLATE_DIR
from jinja2 import Environment, FileSystemLoader
from fun_global import get_current_time
from web.fun_test.web_interface import get_performance_url


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class PerformanceTc(FunTestCase):
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    workspace_ids = [1480]
    atomic_url = get_performance_url() + "/atomic"
    negative_threshold = -5
    positive_threshold = 5
    email_list = [TEAM_REGRESSION_EMAIL]

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _calculate_percentage(self, current, previous):
        percent_num = (float(current - previous) / float(previous)) * 100.0
        percentage = round(percent_num, 2)
        return percentage

    def _send_email(self, email, subject, reports):
        report_name = "performance_drop_report.html"
        file_loader = FileSystemLoader(JINJA_TEMPLATE_DIR)
        env = Environment(loader=file_loader)
        template = env.get_template(report_name)
        content = template.render(all_reports=reports)
        self.email_list.append(email)
        return send_mail(to_addresses=self.email_list, subject=subject, content=content)

    def _set_dict(self, entries, data_set_dict, output_name, name):
        data_set_dict["name"] = name
        data_set_dict["today"] = getattr(entries[0], output_name)
        data_set_dict["yesterday"] = getattr(entries[1], output_name)
        data_set_dict["today_unit"] = getattr(entries[0], output_name + "_unit")
        data_set_dict["yesterday_unit"] = getattr(entries[1], output_name + "_unit")
        data_set_dict["today_date"] = str(timezone.localtime(getattr(entries[0], "input_date_time")))
        data_set_dict["yesterday_date"] = str(timezone.localtime(getattr(entries[1], "input_date_time")))

    def _set_percentage(self, data_set_dict, report, percentage):
        percentage = str(percentage) + '%'
        if "-" not in percentage:
            percentage = "+" + percentage
        data_set_dict["percentage"] = percentage
        report["data_sets"].append(data_set_dict)


class EmailPerformanceDrop(PerformanceTc):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Email performance drops from various/selected workspaces",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def run(self):
        status = fun_test.PASSED
        for workspace_id in self.workspace_ids:
            reports = []
            metrics = InterestedMetrics.objects.filter(workspace_id=workspace_id)
            email = None
            for metric in metrics:
                metric_id = metric.metric_id
                chart = MetricChart.objects.get(metric_id=metric_id)
                data_sets = chart.get_data_sets()
                metric_model_name = chart.metric_model_name
                metric_model = self.app_config.get_metric_models()[metric_model_name]
                report = {}
                report["chart_name"] = metric.chart_name
                report["lineage"] = metric.lineage
                report["url"] = self.atomic_url + "/" + str(metric.metric_id)
                report["positive"] = chart.positive
                report["data_sets"] = []
                email = metric.email
                for data_set in data_sets:
                    entries = metric_model.objects.filter(**data_set["inputs"]).order_by("-input_date_time")[:2]
                    output_name = data_set["output"]["name"]
                    name = data_set["name"]
                    if len(entries) == 2:
                        data_set_dict = {}
                        self._set_dict(entries=entries, data_set_dict=data_set_dict, output_name=output_name, name=name)
                        if data_set_dict["today"] and data_set_dict["yesterday"]:
                            percentage = self._calculate_percentage(current=data_set_dict["today"],
                                                                  previous=data_set_dict[
                                "yesterday"])
                            if chart.positive and percentage < self.negative_threshold:
                                self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)
                            elif not chart.positive and percentage > self.positive_threshold:
                                self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)

                if len(report["data_sets"]):
                    reports.append(report)
            if len(reports):
                print reports
                status = fun_test.FAILED
                subject = "Performance drop report - " + str(get_current_time())
                try:
                    data = self._send_email(email=email, subject=subject, reports=reports)
                    if not data.status:
                        raise Exception("sending email failed to - {}".format(email))
                    else:
                        print "sent email successfully to - {}".format(email)
                except Exception as ex:
                    status = fun_test.FAILED
                    fun_test.critical(str(ex))
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=status, message="No degraded metrics")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(EmailPerformanceDrop())
    myscript.run()
