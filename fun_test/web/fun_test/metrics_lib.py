import os
import django
from web.web_global import PRIMARY_SETTINGS_FILE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
import json
import random, pytz
from dateutil.parser import parse
import re
from fun_global import *
from datetime import datetime
from django.apps import apps
from fun_global import get_localized_time
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging
from fun_settings import MAIN_WEB_APP
from collections import OrderedDict

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
from datetime import datetime, timedelta
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, MileStoneMarkers, LastMetricId, PerformanceMetricsDag
from web.fun_test.models import InterestedMetrics, PerformanceUserWorkspaces, MetricsGlobalSettings
from fun_settings import TEAM_REGRESSION_EMAIL
from web.web_global import JINJA_TEMPLATE_DIR
from jinja2 import Environment, FileSystemLoader
from lib.utilities.send_mail import *
from web.fun_test.web_interface import get_performance_url
from django.utils import timezone
import requests

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
atomic_url = get_performance_url() + "/atomic"
negative_threshold = -5
positive_threshold = 5
DEFAULT_BASE_URL = "http://integration.fungible.local"


class MetricLib():
    def add_data_set(self, metric_id, data_set):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                data_sets = json.loads(chart.data_sets)
                data_sets.append(data_set)
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def delete_data_set(self, metric_id, data_set):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                data_sets = json.loads(chart.data_sets)
                for set in data_sets:
                    if set["name"] == data_set["name"]:
                        data_sets.remove(set)
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def save_data_sets(self, data_sets, chart):
        chart.data_sets = json.dumps(data_sets)
        chart.save()

    def replace_data_sets(self, data_sets, metric_id):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def get_data_sets(self, metric_id):
        result = []
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            result = json.loads(chart.data_sets)
        except Exception as ex:
            print str(ex)
        return result

    def get_peer_ids(self, metric_id):
        result = []
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            result = json.loads(chart.peer_ids)
        except Exception as ex:
            print str(ex)
        return result

    def get_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                if not value == data_set["inputs"][key]:
                                    return []
                        return data_set
                return []
        except:
            return []

    def set_attributes_to_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                if data_set["inputs"][key]:
                                    data_set["inputs"][key] = value
                        break
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def add_attributes_to_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                data_set["inputs"][key] = value
                        break
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def add_attributes_to_data_sets(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                for key, value in kwargs.iteritems():
                    data_set["inputs"][key] = value
            self.save_data_sets(data_sets=data_sets, chart=chart)
            return True
        except:
            return False

    def set_work_in_progress(self, chart, in_progress):
        chart.work_in_progress = in_progress
        chart.save()

    def create_chart(self, **kwargs):
        metric_id = LastMetricId.get_next_id()
        chart = MetricChart(chart_name=kwargs["chart_name"],
                            metric_id=metric_id,
                            internal_chart_name=kwargs["internal_chart_name"],
                            data_sets=kwargs["data_sets"],
                            leaf=kwargs["leaf"],
                            description=kwargs["description"],
                            owner_info=kwargs["owner_info"],
                            source=kwargs["source"],
                            positive=kwargs["positive"],
                            y1_axis_title=kwargs["y1_axis_title"],
                            visualization_unit=kwargs["visualization_unit"],
                            metric_model_name=kwargs["metric_model_name"],
                            base_line_date=kwargs["base_line_date"],
                            work_in_progress=kwargs["work_in_progress"],
                            children=kwargs["children"],
                            jira_ids=kwargs["jira_ids"],
                            platform=kwargs["platform"],
                            peer_ids=kwargs["peer_ids"],
                            creator=kwargs["creator"],
                            workspace_ids=kwargs["workspace_ids"])
        chart.save()
        return chart

    def set_inputs_data_sets(self, data_sets, **kwargs):
        for data_set in data_sets:
            for key, value in kwargs.iteritems():
                data_set["inputs"][key] = value
        return data_sets

    def set_outputs_data_sets(self, data_sets, **kwargs):
        for data_set in data_sets:
            for key, value in kwargs.iteritems():
                data_set["output"][key] = value
        return data_sets

    def remove_attribute_from_data_sets(self, chart, key):
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"].pop(key, None)
        self.save_data_sets(data_sets=data_sets, chart=chart)

    def clone_chart(self, old_chart, internal_chart_name, data_sets):
        if not MetricChart.objects.filter(internal_chart_name=internal_chart_name).exists():
            metric_id = LastMetricId.get_next_id()
            peer_id = []
            peer_id.append(old_chart.metric_id)
            print("Metric id:{}".format(metric_id))
            MetricChart(chart_name=old_chart.chart_name,
                        platform=FunPlatform.S1,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=old_chart.leaf,
                        description=old_chart.description,
                        owner_info=old_chart.owner_info,
                        source=old_chart.source,
                        positive=old_chart.positive,
                        y1_axis_title=old_chart.y1_axis_title,
                        visualization_unit=old_chart.visualization_unit,
                        metric_model_name=old_chart.metric_model_name,
                        base_line_date=old_chart.base_line_date,
                        work_in_progress=False,
                        peer_ids=json.dumps(peer_id)).save()
            old_chart.peer_ids = json.dumps([metric_id])
            old_chart.save()

    def update_weights_for_wip(self):
        charts = MetricChart.objects.filter(metric_model_name="MetricContainer")
        for container in charts:
            children = json.loads(container.children)
            for child in children:
                chart = MetricChart.objects.get(metric_id=child)
                if chart and chart.work_in_progress:
                    container.add_child_weight(child_id=child, weight=0)

    def reset_reference_value(self, chart):
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["output"]["reference"] = -1
            data_set["output"]["expected"] = -1
            data_set["output"]["min"] = 0
            data_set["output"]["max"] = -1
        chart.data_sets = json.dumps(data_sets)
        chart.save()

    def delete_jira_info(self, chart, jira_id):
        try:
            if jira_id:
                jira_ids = json.loads(chart.jira_ids)
                if jira_id in jira_ids:
                    jira_ids.remove(jira_id)
                    chart.jira_ids = json.dumps(jira_ids)
                    chart.save()
        except ObjectDoesNotExist:
            logger.critical("No data found - Deleting jira id {}".format(jira_id))
        return "Ok"

    def validate_jira(self, jira_id):
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

    def remove_resolved_bugs(self):
        charts = MetricChart.objects.all()
        closed_status = ["Resolved", "Closed", "Done"]
        for chart in charts:
            jira_ids = json.loads(chart.jira_ids)
            if (len(jira_ids)):
                for jira_id in jira_ids:
                    jira_info = self.validate_jira(jira_id=jira_id)
                    if jira_info:
                        if jira_info.fields.status.name in closed_status:
                            print chart.chart_name, jira_id
                            self.delete_jira_info(chart=chart, jira_id=jira_id)

    def create_container(self, chart_name, internal_chart_name, owner_info, source, platform, base_line_date, \
                         workspace_ids):
        data_sets = []
        one_data_set = {}
        one_data_set["name"] = "Scores"
        one_data_set["output"] = {"min": 0, "max": 200}
        data_sets.append(one_data_set)
        kwargs = {}
        kwargs["chart_name"] = chart_name
        kwargs["internal_chart_name"] = internal_chart_name
        kwargs["data_sets"] = json.dumps(data_sets)
        kwargs["leaf"] = False
        kwargs["description"] = "TBD"
        kwargs["owner_info"] = owner_info
        kwargs["source"] = source
        kwargs["positive"] = True
        kwargs["y1_axis_title"] = ""
        kwargs["visualization_unit"] = ""
        kwargs["metric_model_name"] = "MetricContainer"
        kwargs["base_line_date"] = base_line_date
        kwargs["work_in_progress"] = False
        kwargs["children"] = "[]"
        kwargs["jira_ids"] = "[]"
        kwargs["platform"] = platform
        kwargs["peer_ids"] = "[]"
        kwargs["creator"] = TEAM_REGRESSION_EMAIL
        kwargs["workspace_ids"] = workspace_ids
        return self.create_chart(**kwargs)

    def create_leaf(self, chart_name, internal_chart_name, data_sets, leaf, description, owner_info, source,
                    positive, y1_axis_title, visualization_unit, metric_model_name, base_line_date,
                    work_in_progress, children, jira_ids, platform, peer_ids, creator, workspace_ids):
        kwargs = {}
        kwargs["chart_name"] = chart_name
        kwargs["internal_chart_name"] = internal_chart_name
        kwargs["data_sets"] = json.dumps(data_sets)
        kwargs["leaf"] = leaf
        kwargs["description"] = description
        kwargs["owner_info"] = owner_info
        kwargs["source"] = source
        kwargs["positive"] = positive
        kwargs["y1_axis_title"] = y1_axis_title
        kwargs["visualization_unit"] = visualization_unit
        kwargs["metric_model_name"] = metric_model_name
        kwargs["base_line_date"] = base_line_date
        kwargs["work_in_progress"] = work_in_progress
        kwargs["children"] = json.dumps(children)
        kwargs["jira_ids"] = json.dumps(jira_ids)
        kwargs["platform"] = platform
        kwargs["peer_ids"] = json.dumps(peer_ids)
        kwargs["creator"] = creator
        kwargs["workspace_ids"] = workspace_ids
        return self.create_chart(**kwargs)

    def _get_new_dict(self, chart):
        dict = OrderedDict()
        dict["name"] = chart.internal_chart_name
        dict["label"] = chart.chart_name
        dict["metric_model_name"] = chart.metric_model_name
        dict["children"] = []
        return dict

    def get_dict(self, chart):
        root_dict = self._get_new_dict(chart=chart)
        children = json.loads(chart.children)
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=int(child))
            child_dict = self.get_dict(chart=child_chart)
            root_dict["children"].append(child_dict)
        return root_dict

    def _send_email(self, email, subject, reports, report_name="performance_drop_report.html"):
        file_loader = FileSystemLoader(JINJA_TEMPLATE_DIR)
        env = Environment(loader=file_loader)
        template = env.get_template(report_name)
        content = template.render(all_reports=reports)
        return send_mail(to_addresses=email, subject=subject, content=content)

    def _generate_report(self, workspace_id):
        reports = []
        metrics = InterestedMetrics.objects.filter(workspace_id=workspace_id)
        for metric in metrics:
            self._set_report_fields(lineage=metric.lineage, metric_id=metric.metric_id, reports=reports, root=True)
        return reports

    def _set_report_fields(self, lineage, metric_id, reports, root=False):
        chart = MetricChart.objects.get(metric_id=metric_id)
        if not root:
            lineage += "/" + chart.chart_name
        if chart.leaf:
            data_sets = chart.get_data_sets()
            metric_model_name = chart.metric_model_name
            metric_model = app_config.get_metric_models()[metric_model_name]
            report = {}
            report["chart_name"] = chart.chart_name
            report["lineage"] = lineage
            report["jira_ids"] = chart.get_jira_ids()
            report["url"] = atomic_url + "/" + str(metric_id)
            report["positive"] = chart.positive
            report["data_sets"] = []
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
                        if chart.positive and percentage < negative_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)
                        elif not chart.positive and percentage > positive_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)

            if len(report["data_sets"]):
                reports.append(report)
        else:
            children = chart.get_children()
            for child in children:
                self._set_report_fields(lineage=lineage, metric_id=int(child), reports=reports, root=False)

    def _calculate_percentage(self, current, previous):
        percent_num = (float(current - previous) / float(previous)) * 100.0
        percentage = round(percent_num, 2)
        return percentage

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

    def _get_email_address(self, workspace_id):
        workspace = PerformanceUserWorkspaces.objects.get(id=workspace_id)
        return workspace.email

    def backup_dags(self):
        metric_ids = [101, 591]
        result = {}
        for metric_id in metric_ids:
            if metric_id == 101:
                dag = "F1"
            else:
                dag = "S1"
            resp = requests.get(DEFAULT_BASE_URL + '/metrics/dag?root_metric_ids=' + str(metric_id))
            if resp.status_code == 200:
                full_json = json.loads(resp.content)
                data = full_json["data"][0]
                print json.dumps(data)
                result[dag] = json.dumps(data)
        f1_dag = result["F1"]
        s1_dag = result["S1"]
        PerformanceMetricsDag(f1_metrics_dag=f1_dag, s1_metrics_dag=s1_dag).save()
        print "dag backup successful"

    def set_global_cache(self, cache_valid):
        global_setting = MetricsGlobalSettings.objects.first()
        global_setting.cache_valid = cache_valid
        global_setting.save()


if __name__ == "__main__":
    ml = MetricLib()
    ml.remove_resolved_bugs()
