import os
import django
from web.web_global import PRIMARY_SETTINGS_FILE, F1_ROOT_ID, S1_ROOT_ID, OTHER_ROOT_ID, FS1600_ROOT_ID

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
from web.fun_test.metrics_models import MetricChart, MileStoneMarkers, LastMetricId, PerformanceMetricsDag, \
    MetricsGlobalSettings
from web.fun_test.models import InterestedMetrics, PerformanceUserWorkspaces
from fun_settings import TEAM_REGRESSION_EMAIL
from web.web_global import JINJA_TEMPLATE_DIR
from jinja2 import Environment, FileSystemLoader
from lib.utilities.send_mail import *
from web.fun_test.web_interface import get_performance_url
from django.utils import timezone
import requests
from fun_settings import WEB_ROOT_DIR

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
atomic_url = get_performance_url() + "/atomic"
negative_threshold = -5
positive_threshold = 5
DEFAULT_BASE_URL = "http://integration.fungible.local"
METRICS_BASE_DATA_FILE = WEB_ROOT_DIR + "/metrics.json"


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

    def create_container(self, chart_name, internal_chart_name, owner_info, platform,
                         base_line_date,
                         workspace_ids=[], source="Unknown"):
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

    def create_leaf(self, chart_name, internal_chart_name, data_sets, owner_info,
                    positive, y1_axis_title, visualization_unit, metric_model_name, base_line_date, platform,
                    leaf=True, description="TBD", source="Unknown", work_in_progress=False, children=[], jira_ids=[],
                    peer_ids=[], creator=TEAM_REGRESSION_EMAIL, workspace_ids=[]):
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

    def add_child_to_metrics_json(self, parent_internal_chart_name, child_dict):
        if is_development_mode():
            with open(METRICS_BASE_DATA_FILE, "r") as file:
                metrics = json.load(file, object_pairs_hook=OrderedDict)
                if len(metrics):
                    returned_dict = self.recurse_and_add_child(metrics_dict=metrics,
                                                        internal_chart_name=parent_internal_chart_name,
                                      child_dict=child_dict)
                    if returned_dict["added"]:
                        with open(METRICS_BASE_DATA_FILE, "w") as out:
                            json.dump(returned_dict["dict"], out, indent=2)

    def recurse_and_add_child(self, metrics_dict, internal_chart_name, child_dict, return_dict={"added": False}):
        for metric in metrics_dict:
            if not return_dict["added"]:
                if metric["metric_model_name"] == "MetricContainer" and "reference" not in metric:
                    if internal_chart_name == metric["name"]:
                        metric["children"].append(child_dict)
                        return_dict["added"] = True
                        return_dict["dict"] = metrics_dict
                        break
                    else:
                        return_dict = self.recurse_and_add_child(metrics_dict=metric["children"],
                                                                 internal_chart_name=internal_chart_name,
                                                                 child_dict=child_dict, return_dict=return_dict)
                        if return_dict["added"]:
                            break
        return return_dict


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
        if len(metrics):
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
                    if data_set_dict["today"] and data_set_dict["yesterday"] and data_set_dict["today"] != -1 and \
                            data_set_dict["yesterday"] != -1:
                        percentage = self._calculate_percentage(current=data_set_dict["today"],
                                                                previous=data_set_dict[
                                                                    "yesterday"])
                        best_percentage = self._calculate_percentage(current=data_set_dict["today"],
                                                                     previous=data_set["output"]["best"]) if \
                            data_set["output"]["best"] != -1 else None

                        if chart.positive and percentage < negative_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)
                        elif not chart.positive and percentage > positive_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=percentage)
                        elif chart.positive and best_percentage and best_percentage < negative_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=best_percentage)
                        elif not chart.positive and best_percentage and best_percentage > positive_threshold:
                            self._set_percentage(data_set_dict=data_set_dict, report=report, percentage=best_percentage)

            if len(report["data_sets"]):
                reports.append(report)
        else:
            children = chart.get_children()
            for child in children:
                self._set_report_fields(lineage=lineage, metric_id=int(child), reports=reports, root=False)

    def _calculate_percentage(self, current, previous):
        percentage = 0
        if previous:
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
        self.set_global_cache(cache_valid=False)
        metric_ids = [F1_ROOT_ID, S1_ROOT_ID, FS1600_ROOT_ID, OTHER_ROOT_ID]  # F1, S1, FS1600, Other metric id
        result = self.fetch_dag(metric_ids=metric_ids, backup=True)
        PerformanceMetricsDag(metrics_dag=json.dumps(result)).save()
        print "dag backup successful"

    def traverse_dag(self, levels, metric_id, metric_chart_entries, sort_by_name=True):
        result = {}
        if metric_id not in metric_chart_entries:
            chart = MetricChart.objects.get(metric_id=metric_id)
        else:
            chart = metric_chart_entries[metric_id]

        result["metric_model_name"] = chart.metric_model_name
        result["chart_name"] = chart.chart_name
        if levels < 1:
            result['children'] = []
        else:
            result["children"] = json.loads(chart.children)
        result["children_info"] = {}
        result["children_weights"] = json.loads(chart.children_weights)
        result["leaf"] = chart.leaf
        result["num_leaves"] = chart.num_leaves
        result["last_num_degrades"] = chart.last_num_degrades
        result["last_num_build_failed"] = chart.last_num_build_failed
        result["positive"] = chart.positive
        result["work_in_progress"] = chart.work_in_progress
        result["companion_charts"] = chart.companion_charts
        result["jira_ids"] = json.loads(chart.jira_ids)
        result["metric_id"] = chart.metric_id

        result["copied_score"] = chart.copied_score
        result["copied_score_disposition"] = chart.copied_score_disposition
        if chart.last_good_score >= 0:
            result["last_two_scores"] = [chart.last_good_score, chart.penultimate_good_score]
        else:
            result["last_two_scores"] = [0, 0]
        if levels >= 1 and not chart.leaf:
            levels = levels - 1
            children_info = result["children_info"]
            for child_id in result["children"]:
                if child_id in metric_chart_entries:
                    child_chart = metric_chart_entries[child_id]
                else:
                    child_chart = MetricChart.objects.get(metric_id=child_id)
                    metric_chart_entries[child_id] = child_chart
                children_info[child_chart.metric_id] = self.traverse_dag(levels=levels, metric_id=child_chart.metric_id,
                                                                         metric_chart_entries=metric_chart_entries)
            if sort_by_name:
                result["children"] = map(lambda item: item[0],
                                         sorted(children_info.iteritems(), key=lambda d: d[1]['chart_name']))
        return result

    def fetch_dag(self, metric_ids, levels=15, is_workspace=0, backup=False):
        result = []
        cache_valid = MetricsGlobalSettings.get_cache_validity()
        if not cache_valid or (cache_valid and levels != 15) or int(is_workspace) or backup:
            metric_chart_entries = {}
            for metric_id in metric_ids:
                sort_by_name = False
                chart = MetricChart.objects.get(metric_id=int(metric_id))
                metric_chart_entries[chart.metric_id] = chart
                result.append(self.traverse_dag(levels=levels, metric_id=chart.metric_id, sort_by_name=sort_by_name,
                                                metric_chart_entries=metric_chart_entries))
        else:
            pmds = PerformanceMetricsDag.objects.all().order_by("-date_time")[:1]
            for pmd in pmds:
                result = json.loads(pmd.metrics_dag)
        return result

    def set_global_cache(self, cache_valid):
        global_setting = MetricsGlobalSettings.objects.first()
        global_setting.cache_valid = cache_valid
        global_setting.save()

    def _set_chart_status(self, models, suite_execution_id):
        for model in models:
            charts = MetricChart.objects.filter(metric_model_name=model)
            metric_model = app_config.get_metric_models()[model]
            for chart in charts:
                status = True
                data_sets = chart.get_data_sets()
                for data_set in data_sets:
                    inputs = data_set["inputs"]
                    entries = metric_model.objects.filter(**inputs).order_by("-input_date_time")[:1]
                    if len(entries):
                        entry = entries.first()
                        if not entry.status == RESULTS["PASSED"]:
                            status = False
                            chart.set_chart_status(status=RESULTS["FAILED"],
                                                   suite_execution_id=suite_execution_id)
                            break
                if status:
                    chart.set_chart_status(status=RESULTS["PASSED"], suite_execution_id=suite_execution_id)


if __name__ == "__main__":
    ml = MetricLib()
    ml.remove_resolved_bugs()
