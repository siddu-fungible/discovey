from fun_settings import MAIN_WEB_APP
from django.db import models
from django.apps import apps
#from web.fun_test import apps
from fun_global import RESULTS, get_current_time, get_localized_time, FunPlatform
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
import json
# from web.fun_test.site_state import site_state
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME, TEAM_REGRESSION_EMAIL
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
import logging
import datetime
from datetime import datetime, timedelta
from django.contrib.postgres.fields import JSONField, ArrayField
from web.web_global import *
from web.fun_test.triaging_global import TriagingStates, TriageTrialStates, TriagingResult, TriagingTypes
from fun_global import PerfUnit, ChartType, FunChartType
from web.fun_test.models import FunModel

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

LAST_ANALYTICS_DB_STATUS_UPDATE = "last_status_update"
BASE_LINE_DATE = datetime(year=2018, month=4, day=1)

class MetricsGlobalSettings(models.Model):
    tolerance_percentage = models.FloatField(default=3.0)
    cache_valid = models.BooleanField(default=True)

    @staticmethod
    def get_cache_validity():
        first_record = MetricsGlobalSettings.objects.first()
        return first_record.cache_valid

class MetricsGlobalSettingsSerializer(ModelSerializer):

    class Meta:
        model = MetricsGlobalSettings
        fields = "__all__"


class MetricsRunTime(models.Model):
    name = models.TextField(default="", unique=True)
    value = JSONField(default={})

    def __str__(self):
        return "{}: {}".format(self.name, self.value)

    @staticmethod
    def update_value_data(name, value_key, value_data):
        run_times = MetricsRunTime.objects.filter(name=name)
        if run_times.exists():
            run_time = run_times[0]
            run_time.value[value_key] = value_data
            run_time.save()

class SchedulingStates:
    ACTIVE = "Active"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SUCCESS = "Success"
    SUSPENDED = "Suspended"
    RUNNING = "Running"
    KILLED = "Killed"
    SUBMITTED = "Submitted"
    IN_JENKINS = "In Jenkins"
    WAITING = "Waiting"
    SELECTED_FOR_TRIAL = "Selected for trial"
    BUILD_COMPLETE = "Build complete"
    IN_LSF = "In Lsf"
    PASSED = "Passed"
    ABORTED = "Aborted"
    SUBMITTED_TO_JENKINS = "Submitted to Jenkins"
    BUILDING_ON_JENKINS = "Building on Jenkins"
    JENKINS_BUILD_COMPLETE = "Jenkins build complete"
    QUEUED_ON_LSF = "Queued on Lsf"
    RUNNING_ON_LSF = "Running on Lsf"
    IN_PROGRESS = "In progress"


class MetricChartStatus(models.Model):
    metric_id = models.IntegerField(default=-1, db_index=True)
    chart_name = models.TextField(default="Unknown")
    data_sets = JSONField()
    date_time = models.DateTimeField(default=datetime.now)
    score = models.FloatField(default=-1)
    suite_execution_id = models.IntegerField(default=-1)
    jenkins_job_id = models.IntegerField(default=-1)
    lsf_job_id = models.IntegerField(default=-1)
    build_status = models.CharField(max_length=15, default=RESULTS["UNKNOWN"])
    test_case_id = models.IntegerField(default=-1)
    valid = models.BooleanField(default=False)
    git_commit = models.TextField(default="")
    copied_score = models.BooleanField(default=False)  # If the score was copied from the last good score
    copied_score_disposition = models.IntegerField(default=0)  # 0 indicates current and last score is identical,
                                                               # 1 indicates last copied score was in upward trend
                                                               # -1 indicates last copied score was in downward trend
    if get_default_db_engine() == DB_ENGINE_TYPE_POSTGRES:
        children_score_map = JSONField(default={})
    else:
        children_score_map = models.TextField(default="{}")

    def __str__(self):
        s = "{}:{} {} Score: {}".format(self.metric_id, self.chart_name, self.date_time, self.score)
        return s

    class Meta:
        indexes = [
            models.Index(fields=['metric_id'])
        ]


class Triage3(models.Model):
    # Submission
    metric_id = models.IntegerField(null=True)
    triage_id = models.IntegerField(unique=True)
    build_parameters = JSONField(null=True)
    # blob = JSONField(default=None, null=True)  # for anything other than Jenkins parameters, like Integration parameters
    triage_type = models.IntegerField(default=TriagingTypes.REGEX_MATCH)
    from_fun_os_sha = models.TextField()  # The initial lower bound
    to_fun_os_sha = models.TextField()    # The initial upper bound
    submitter_email = models.EmailField(default="john.abraham@fungible.com")
    regex_match_string = models.TextField(default="")

    submission_date_time = models.DateTimeField(default=datetime.now)
    status = models.IntegerField(default=TriagingStates.UNKNOWN)
    result = models.TextField(default=TriagingResult.UNKNOWN)

    current_trial_set_id = models.IntegerField(default=-1)
    current_trial_set_count = models.IntegerField(default=-1)
    current_trial_from_sha = models.TextField(default="")
    current_trial_to_sha = models.TextField(default="")

    base_tag = models.TextField(default="qa_triage")

    @staticmethod
    def get_tag(base_tag, other_tag):
        return "{}_{}".format(base_tag, other_tag)


class Triage3Trial(models.Model):
    triage_id = models.IntegerField()
    fun_os_sha = models.TextField()
    trial_set_id = models.IntegerField(default=-1)
    status = models.IntegerField(default=TriagingStates.UNKNOWN)
    jenkins_build_number = models.IntegerField(default=-1)
    lsf_job_id = models.IntegerField(default=-1)
    tag = models.TextField(default="")
    regex_match = models.TextField(default="")
    submission_date_time = models.DateTimeField(default=datetime.now)
    tags = JSONField(default=[])  # for re-runs
    result = models.TextField(default=RESULTS["UNKNOWN"])
    original_id = models.IntegerField(default=-1)
    active = models.BooleanField(default=True)
    reruns = models.BooleanField(default=False)

    integration_job_id = models.IntegerField(default=-1)

    def __str__(self):
        return "Trial: Triage: {} Tag: {} Sha: {} Set: {} Status: {}".format(self.triage_id,
                                                                             self.tag,
                                                                             self.fun_os_sha,
                                                                             self.trial_set_id,
                                                                             TriageTrialStates().code_to_string(self.status))

    def __repr__(self):
        return self.__str__()


class TimestampField(serializers.Field):
    def to_representation(self, value):
        epoch = get_localized_time(datetime(1970, 1, 1))
        return int((value - epoch).total_seconds())

class MetricChartStatusSerializer(ModelSerializer):
    date_time = TimestampField()

    class Meta:
        model = MetricChartStatus
        fields = "__all__"

class MetricChart(models.Model):
    last_build_status = models.CharField(max_length=15, default=RESULTS["PASSED"])
    last_build_date = models.DateTimeField(verbose_name="last_build_date", default=datetime.now)
    data_sets = models.TextField(default="[]")
    chart_name = models.TextField()
    internal_chart_name = models.TextField(default="UNKNOWN", unique=True)
    metric_model_name = models.TextField(default="Performance1")
    description = models.TextField(default="TBD")
    metric_id = models.IntegerField(default=10)
    children = models.TextField(default="[]")
    leaf = models.BooleanField(default=False)
    positive = models.BooleanField(default=True)
    y1_axis_title = models.TextField(default="")
    y2_axis_title = models.TextField(default="")
    children_weights = models.TextField(default="{}")
    goodness_cache = models.TextField(default="[]")
    goodness_cache_range = models.IntegerField(default=5)
    goodness_cache_valid = models.BooleanField(default=False)
    status_cache = models.TextField(default="[]")
    score_cache_valid = models.BooleanField(default=False)
    last_num_degrades = models.IntegerField(default=0)
    last_status_update_date = models.DateTimeField(verbose_name="last_status_update", default=datetime.now)
    last_num_build_failed = models.IntegerField(default=0)
    num_leaves = models.IntegerField(default=0)
    last_good_score = models.FloatField(default=-1)
    penultimate_good_score = models.FloatField(default=-1)
    copied_score = models.BooleanField(default=False)
    copied_score_disposition = models.IntegerField(default=0)
    last_suite_execution_id = models.IntegerField(default=-1)
    last_jenkins_job_id = models.IntegerField(default=-1)
    last_test_case_id = models.IntegerField(default=-1)
    last_lsf_job_id = models.IntegerField(default=-1)
    last_git_commit = models.TextField(default="")
    owner_info = models.TextField(default="UNKNOWN")
    source = models.TextField(default="Unknown")
    jira_ids = models.TextField(default="[]")
    base_line_date = models.DateTimeField(verbose_name="base_line_date", default=BASE_LINE_DATE)
    visualization_unit = models.CharField(max_length=20, default="")
    work_in_progress = models.BooleanField(default=False)
    peer_ids = models.TextField(default="[]")
    platform = models.TextField(default=FunPlatform.F1)
    companion_charts = ArrayField(models.IntegerField(default=-1), default=[], blank=True)
    creator = models.TextField(default=TEAM_REGRESSION_EMAIL)
    workspace_ids = JSONField(default=[])

    def __str__(self):
        return "{}: {} : {} : {}".format(self.internal_chart_name, self.chart_name, self.metric_model_name, self.metric_id)

    def get_children(self):
        return json.loads(self.children)

    def get_children_weights(self):
        return json.loads(self.children_weights)

    def get_data_sets(self):
        return json.loads(self.data_sets)

    def get_jira_ids(self):
        return json.loads(self.jira_ids)

    def set_chart_status(self, status, suite_execution_id):
        self.last_build_status = status
        self.last_suite_execution_id = suite_execution_id
        self.last_build_date = get_current_time()
        self.save()

    def add_child(self, child_id):
        children = json.loads(self.children)
        if child_id not in children:
            children.append(child_id)
            self.children = json.dumps(children)
            self.save()

    def remove_child(self, child_id):
         children = json.loads(self.children)
         for child in children:
             if int(child) == child_id:
                 children.remove(child)
                 self.children = json.dumps(children)
                 self.save()

    def add_child_weight(self, child_id, weight):
        children_weights = json.loads(self.children_weights)
        children_weights = {int(x): y for x, y in children_weights.iteritems()}
        children_weights[int(child_id)] = weight
        self.children_weights = json.dumps(children_weights)
        self.save()

    def add_bugs(self, jira_id):
        jira_ids = json.loads(self.jira_ids)
        if jira_id not in jira_ids:
            jira_ids.append(jira_id)
            self.jira_ids = json.dumps(jira_ids)
            self.save()

    def remove_bugs(self, jira_id):
        jira_ids = json.loads(self.jira_ids)
        if jira_id in jira_ids:
            jira_ids.remove(jira_id)
            self.jira_ids = json.dumps(jira_ids)
            self.save()

    def fix_children_weights(self):
        children = json.loads(self.children)
        children_weights = json.loads(self.children_weights)
        children_weights = {int(x): y for x, y in children_weights.iteritems()}
        new_children_weights = {}
        for child in children:
            child_id = int(child)
            new_children_weights[child_id] = children_weights.get(child_id, 1)
        self.children_weights = json.dumps(new_children_weights)
        self.save()

    def goodness(self):
        children = json.loads(self.children)
        goodness = 0
        if len(children):
            goodness = 0
            for child in children:
                metric = MetricChart.objects.get(metric_id=child)
                goodness += metric.goodness()
        else:
            # Must be a leaf
            # get_last_value
            # get expected value
            pass
        return goodness

    def get_output_data_set(self, output_name):
        result = {}
        data_sets = json.loads(self.data_sets)
        for data_set in data_sets:
            if data_set["output"]["name"] == output_name:
                result["min"] = data_set["output"]["min"]
                result["max"] = data_set["output"]["max"]
                break
        return result

    def get_last_record(self, number_of_records=1, data_set=None):
        return self.filter(number_of_records=number_of_records, data_set=data_set)

    def get_first_record(self, number_of_records=1, data_set=None):
        return self.filter(number_of_records=number_of_records, data_set=data_set, chronologically_recent=False)

    def get_leaves(self):
        data = {}
        data["name"] = self.chart_name
        data["metric_model_name"] = self.metric_model_name
        if not self.leaf:
            data["children"] = []
            data["leaf"] = False
        else:
            data["leaf"] = True
        children = json.loads(self.children)
        if not self.leaf:
            if len(children):
                for child in children:
                    child_metric = MetricChart.objects.get(metric_id=child)
                    child_leaves = child_metric.get_leaves()
                    data["children"].append(child_leaves)
        else:
            data["id"] = self.metric_id

        return data

    def get_day_bounds(self, dt):
        d = self.get_rounded_time(dt)
        start = d.replace(hour=0, minute=0, second=0)
        end = d.replace(hour=23, minute=59, second=59)
        return start, end

    def get_rounded_time(self, dt):
        rounded_d = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59)
        rounded_d = get_localized_time(rounded_d)
        return rounded_d

    def get_entries_for_day(self, metric, day, data_set):
        bounds = self.get_day_bounds(day)
        d = {}
        d["input_date_time__range"] = bounds
        inputs = data_set["inputs"]
        for input_name, input_value in inputs.iteritems():
            if d == "input_date_time":
                continue
            d[input_name] = input_value
        result = metric.objects.filter(**d)
        # if result.count() > 1:
        #    result = result.last()
        return result

    def fixup(self, metric, from_date, to_date, data_set):
        # self.remove_duplicates(metric)
        current_date = self.get_rounded_time(to_date)
        holes = {}
        day_entries = None
        new_hole = None
        while current_date >= from_date:
            entry = self.get_entries_for_day(metric=metric, day=current_date, data_set=data_set)

            if not entry.count():
                if current_date in holes:
                    # fill this hole with last available entry
                    for day_entry in day_entries:
                        day_entry.pk = None
                        day_entry.interpolated = True
                        day_entry.input_date_time = current_date
                        day_entry.save()
                else:
                    # Lets find the last available entry from here
                    i = 0
                    while i < 366: #TODO: Can't find an entry in the last 366 days?
                        day = current_date - timedelta(days=i)
                        day_entries = self.get_entries_for_day(metric=metric, day=day, data_set=data_set)
                        if day_entries.count():
                            for day_entry in day_entries:
                                day_entry.pk = None
                                day_entry.interpolated = True
                                day_entry.input_date_time = current_date
                                day_entry.save()
                            break
                        else:
                            new_hole = self.get_rounded_time(day)
                            holes[new_hole] = False
                        i = i + 1
            else:
                day_entries = None
            current_date = current_date - timedelta(days=1)  # TODO: if we know the holes jump to the next hole

    def fixup_reference_values(self, data_set):
        modified = 0
        # if self.chart_name == "BLK_LSV: Latency":
        #    j = 0
        first_record = self.get_first_record(data_set=data_set, number_of_records=100)
        if not first_record:
            data_set["output"]["reference"] = 0
            modified = 1
        else:
            output_name = data_set["output"]["name"]
            for first in first_record[::-1]:
                if output_name in first:
                    if first[output_name] > 0:
                        data_set["output"]["reference"] = first[output_name]
                        modified = 1
                        break
            if modified == 0:
                data_set["output"]["reference"] = 0
                modified = 1
            # data_set["expected"] = first_rec
        # self.data_sets = json.dumps(data_set)
        # self.save()
        return modified

    def is_same_day(self, d1, d2):
        return (d1.year == d2.year) and (d1.month == d2.month) and (d1.day == d2.day)


    def get_status(self):
        children = json.loads(self.children)
        children_info = {}
        if not self.leaf:
            if len(children):
                for child in children:
                    child_metric = MetricChart.objects.get(metric_id=child)
                    serialized = MetricChartSerializer(child_metric, many=False)
                    serialized_data = serialized.data
                    get_status = child_metric.get_status()
                    serialized_data.update(get_status)
                    children_info[child] = serialized_data
        else:
            pass

        return {
                "children_info": children_info}

    def get_status2(self, number_of_records=5):
        print ("Get status for: {}".format(self.chart_name))
        goodness_values = []
        status_values = []
        children = json.loads(self.children)
        children_weights = json.loads(self.children_weights)
        children_weights = {int(x): y for x, y in children_weights.iteritems()}
        children_goodness_map = {}
        num_children_passed = 0
        num_children_failed = 0
        num_degrades = 0
        num_child_degrades = 0
        leaf_status = True

        children_info = {}
        if not self.leaf:
            if len(children):
                child_degrades = 0
                sum_of_child_weights = 0
                for child in children:

                    child_metric = MetricChart.objects.get(metric_id=child)
                    child_weight = children_weights[child] if child in children_weights else 1
                    sum_of_child_weights += child_weight
                    get_status = child_metric.get_status(number_of_records=number_of_records)

                    serialized = MetricChartSerializer(child_metric, many=False)
                    serialized_data = serialized.data
                    serialized_data.update(get_status)

                    children_info[child] = serialized_data
                    child_status_values, child_goodness_values = get_status["status_values"], \
                                                                 get_status["goodness_values"]
                    if child_metric.leaf:
                        num_child_degrades += get_status["num_degrades"]
                    else:
                        num_child_degrades += get_status["num_child_degrades"]

                    last_child_status = child_status_values[-1]
                    if last_child_status:
                        num_children_passed += 1
                    else:
                        num_children_failed += 1

                    for i in range(number_of_records - 1):
                        if len(status_values) < (i + 1):
                            status_values.append(True)
                        if len(child_status_values) < (i + 1):
                            child_status_values.append(True)
                        status_values[i] = status_values[i] and child_status_values[i]
                        if len(goodness_values) < (i + 1):
                            goodness_values.append(0)
                        if len(child_goodness_values) < (i + 1):
                            child_goodness_values.append(0)



                        goodness_values[i] += child_goodness_values[i] * child_weight
                        children_goodness_map[child] = child_goodness_values
                if sum_of_child_weights:
                    for i in range(number_of_records - 1):
                        goodness_values[i] = goodness_values[i]/sum_of_child_weights

        else:

            if True and self.goodness_cache_valid and (number_of_records == self.goodness_cache_range):
                goodness_values.extend(json.loads(self.goodness_cache))
                status_values.extend(json.loads(self.status_cache))
            else:
                data_set_mofified = False
                data_sets = json.loads(self.data_sets)
                if len(data_sets):
                    # data_set = data_sets[0]
                    data_set_statuses = []
                    last_records_map = {}
                    for data_set_index, data_set in enumerate(data_sets):
                        last_records = self.get_last_record(number_of_records=number_of_records, data_set=data_set)
                        if len(last_records) < number_of_records:
                            j = 0
                        last_records_map[data_set_index] = {"records": last_records, "goodness": 0}
                        try:
                            # if last_records and (last_records[-1]["status"] == RESULTS["FAILED"]):
                            if self.last_build_status != RESULTS["PASSED"]:
                                leaf_status = False
                        except:
                            pass

                    today = get_current_time()
                    from_date = today - timedelta(days=number_of_records - 1)

                    for day_index in range(number_of_records - 1):
                        current_date = from_date + timedelta(days=day_index)
                        data_set_combined_goodness = 0
                        for data_set_index, data_set in enumerate(data_sets):

                            if last_records_map[data_set_index]["records"]:
                                last_records = last_records_map[data_set_index]["records"]
                                missing_dates = False
                                if len(last_records) < (number_of_records - 1):
                                    missing_dates = True

                                this_days_record = None
                                try:
                                    for last_record in last_records:
                                        if self.is_same_day(last_record["input_date_time"], current_date):

                                            this_days_record = last_record
                                except Exception as ex:
                                    pass
                                if not this_days_record:
                                    continue
                                if missing_dates:
                                    if not self.is_same_day(this_days_record["input_date_time"], current_date):
                                        continue
                                max_value = data_set["output"]["max"]
                                min_value = data_set["output"]["min"]
                                try:
                                    output_name = data_set["output"]["name"]   # TODO
                                except:
                                    pass
                                if "expected" in data_set["output"]:
                                    expected_value = data_set["output"]["expected"]
                                else:
                                    # let's fix it up
                                    data_set_mofified = data_set_mofified or self.fixup_expected_values(data_set=data_set)
                                    expected_value = max_value
                                    if not self.positive:
                                        expected_value = min_value
                                output_value = this_days_record[output_name]

                                data_set_statuses.append(leaf_status)
                                if expected_value is not None:
                                    if self.positive:
                                        data_set_combined_goodness += (float(output_value) / expected_value) * 100 if output_value >= 0 else 0
                                    else:
                                        if output_value:
                                            data_set_combined_goodness += (float(expected_value) / output_value) * 100 if output_value >= 0 else 0
                                        else:
                                            print "ERROR: {}, {}".format(self.chart_name,
                                                                             self.metric_model_name)
                        # data_set_combined_goodness = round(data_set_combined_goodness, 1)

                        goodness_values.append(round(data_set_combined_goodness/len(data_sets), 1))

                    if data_set_statuses:
                        status_values.append(reduce(lambda x, y: x and y, data_set_statuses))
                    else:
                        if not leaf_status:
                            status_values.append(False)
                        else:
                            status_values.append(True)  # Some data-sets may not exist
                if data_set_mofified:
                    self.data_sets = json.dumps(data_sets)
                    self.save()

        # Fill up missing values
        '''
        for i in range(number_of_records - len(goodness_values)):
            if len(goodness_values):
                goodness_values.append(goodness_values[-1])
            else:
                goodness_values.append(0)
        '''
        for i in range(number_of_records - len(status_values)):
            if len(status_values):
                status_values.append(status_values[-1])
            else:
                status_values.append(True)
        # print("Chart_name: {}, Status: {}, Goodness: {}".format(self.chart_name, status_values, goodness_values))
        if self.leaf and not leaf_status:
            goodness_values[-1] = 0
        self.goodness_cache = json.dumps(goodness_values)
        self.goodness_cache_valid = True
        self.goodness_cache_range = number_of_records
        self.status_cache = json.dumps(status_values)
        self.save()  #TODO: Save only if something changed
        try:
            if (goodness_values[-2] > goodness_values[-1]) or (goodness_values[-1] == 0):
                num_degrades += 1
        except:
            num_degrades = 0

        return {"status_values": status_values,
                "goodness_values": goodness_values,
                "children_goodness_map": children_goodness_map,
                "num_children_passed": num_children_passed,
                "num_children_failed": num_children_failed,
                "num_degrades": num_degrades,
                "num_child_degrades": num_child_degrades,
                "children_info": children_info}

    def remove_duplicates(self, model, from_date, to_date):
        vs = vars(model)
        inputs = []
        outputs = []
        for v in vs:
            if v.startswith("input_"):
                inputs.append(v)
            if v.startswith("output_"):
                outputs.append(v)
        for row in model.objects.all():
            d = {}
            for input in inputs:
                d[input] = getattr(row, input)
            for output in outputs:
                d[output] = getattr(row, output)
            if "input_date_time" in inputs:
                del d["input_date_time"]
                d["input_date_time__range"] = [from_date, to_date]
            f = model.objects.filter(**d)
            if f.count() > 1:
                f.delete()

    def filter(self, number_of_records=1, data_set=None, chronologically_recent=True):

        data = []
        # data_sets = json.loads(self.data_sets)
        if data_set:
            # data_set = data_sets[0]
            inputs = data_set["inputs"]
            #model = apps.get_model(app_label='fun_test', model_name=self.metric_model_name)
            model = app_config.get_metric_models()[self.metric_model_name]

            today = get_current_time()
            yesterday = today - timedelta(days=1)
            yesterday = yesterday.replace(hour=23, minute=59, second=59)

            earlier_day = today - timedelta(days=number_of_records - 1)
            earlier_day = earlier_day.replace(hour=0, minute=0, second=1)
            if earlier_day <= self.base_line_date:
                earlier_day = self.base_line_date

            d = {}
            for input_name, input_value in inputs.iteritems():
                if d == "input_date_time":
                    continue
                d[input_name] = input_value
            d["input_date_time__range"] = [earlier_day, today]
            order_by = "-input_date_time"
            if not chronologically_recent:
                order_by = "input_date_time"
            try:
                entries = model.objects.filter(**d).order_by(order_by)
                i = entries.count()
                if i > (number_of_records - 1):
                    entries = model.objects.filter(**d).order_by(order_by)
                    if model.objects.first() and model.objects.first().interpolation_allowed:
                        self.remove_duplicates(model=model, from_date=earlier_day, to_date=today)
                        entries = model.objects.filter(**d).order_by(order_by)
                        i = entries.count()
                if entries.count() < (number_of_records - 1):
                    # let's fix it up
                    if model.objects.first() and hasattr(model.objects.first(), "interpolation_allowed") and\
                            model.objects.first().interpolation_allowed:
                        self.fixup(metric=model, from_date=earlier_day, to_date=yesterday, data_set=data_set)
                    entries = model.objects.filter(**d).order_by(order_by)
                entries = reversed(entries)
                for entry in entries:
                    data.append(model_to_dict(entry))
            except ObjectDoesNotExist:
                logger.critical("No data found Model: {} Inputs: {}".format(self.metric_model_name, str(inputs)))
        return data

    @staticmethod
    def get(chart_name, metric_model_name):
        result = None
        try:
            object = MetricChart.objects.get(chart_name=chart_name, metric_model_name=metric_model_name)
            result = object
        except ObjectDoesNotExist:
            pass
        return result

    def get_metrics_json_blob(self):
        return {"metric_model_name": self.metric_model_name,
                "name": self.internal_chart_name,
                "label": self.chart_name}

class MetricChartSerializer(ModelSerializer):
    class Meta:
        model = MetricChart
        fields = "__all__"


class LastMetricId(models.Model):
    last_id = models.IntegerField(unique=True, default=100)

    @staticmethod
    def get_next_id():
        if not LastMetricId.objects.count():
            LastMetricId().save()
        last = LastMetricId.objects.all().last()
        last.last_id = last.last_id + 1
        last.save()
        return last.last_id

class LastTriageId(models.Model):
    last_id = models.IntegerField(unique=True, default=100)

    @staticmethod
    def get_next_id():
        if not LastTriageId.objects.count():
            LastTriageId().save()
        last = LastTriageId.objects.all().last()
        last.last_id = last.last_id + 1
        last.save()
        return last.last_id

class LastTrialId(models.Model):
    last_id = models.IntegerField(unique=True, default=100)

    @staticmethod
    def get_next_id():
        if not LastTrialId.objects.count():
            LastTrialId().save()
        last = LastTrialId.objects.all().last()
        last.last_id = last.last_id + 1
        last.save()
        return last.last_id

class Chart(models.Model):
    chart_type = models.TextField(default=ChartType.REGULAR)
    title = models.TextField(default="")
    fun_chart_type = models.TextField(default=FunChartType.LINE_CHART)
    x_axis_title = models.TextField(default="")
    y_axis_title = models.TextField(default="")
    series_filters = JSONField(default=[])
    chart_id = models.IntegerField(default=-1, unique=True)
    x_scale = models.TextField(default="")
    y_scale = models.TextField(default="")

    def __str__(self):
        return "{}: {} : {} : {}".format(self.chart_type, self.fun_chart_type, self.x_axis_title,
                                         self.y_axis_title, self.chart_id)


class LastChartId(models.Model):
    last_id = models.IntegerField(unique=True, default=100)

    @staticmethod
    def get_next_id():
        if not LastChartId.objects.count():
            LastChartId().save()
        last = LastChartId.objects.all().last()
        last.last_id = last.last_id + 1
        last.save()
        return last.last_id


class ModelMapping(models.Model):
    module = models.TextField()
    component = models.TextField()
    model_name = models.TextField(default="Performance1", unique=True)

    def __str__(self):
        return "{} {} {}".format(self.model_name, self.module, self.component)


class Performance1(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1 = models.CharField(max_length=30, choices=[(0, "input1_0"), (1, "input1_1")], verbose_name="Input 1 description")
    input2 = models.IntegerField(choices=[(0, 123), (1, 345)], verbose_name="Input 2 description")
    output1 = models.IntegerField(verbose_name="Output 1 description")
    output2 = models.IntegerField(verbose_name="Output 2 description")
    output3 = models.CharField(max_length=30, verbose_name="Output 3 description")
    module = models.TextField(default="networking")
    component = models.TextField(default="general")


class ShaxPerformance(models.Model):
    output_latency_min = models.IntegerField(verbose_name="Latency Min", default=-1)
    output_latency_avg = models.IntegerField(verbose_name="Latency Avg", default=-1)
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_algorithm = models.TextField(verbose_name="Algorithm", default="", choices=[[0, "SHA1"], [1, "SHA224"], [2, "SHA256"], [3, "SHA384"], [4, "SHA512"], [5, "SHA3_224"], [6, "SHA3_256"], [7, "SHA3_384"], [8, "SHA3_512"], [9, "SHA1"], [10, "SHA224"], [11, "SHA256"], [12, "SHA384"], [13, "SHA512"], [14, "SHA3_224"], [15, "SHA3_256"], [16, "SHA3_384"], [17, "SHA3_512"]])
    output_avg_throughput_expected = models.FloatField(verbose_name="Average Throughput expected", default=-1)
    input_num_hw_threads = models.IntegerField(verbose_name="Number of HW threads", default=-1, choices=[[0, 1.0], [1, 1.0], [2, 1.0], [3, 1.0], [4, 1.0], [5, 1.0], [6, 1.0], [7, 1.0], [8, 1.0], [9, ""], [10, 6.0], [11, 6.0], [12, 6.0], [13, 6.0], [14, 6.0], [15, 6.0], [16, 6.0], [17, ""]])
    output_iops_expected = models.IntegerField(verbose_name="IOPS", default=-1)
    output_latency_max = models.IntegerField(verbose_name="Latency Max", default=-1)
    input_sdk_version = models.TextField(verbose_name="Sdk version", default="")
    output_iops = models.IntegerField(verbose_name="IOPS", default=-1)
    output_avg_throughput = models.FloatField(verbose_name="Average Throughput", default=-1)
    input_effort = models.IntegerField(verbose_name="Effort", default=-1, choices=[[0, 1.0], [1, 1.0], [2, 1.0], [3, 1.0], [4, 1.0], [5, 1.0], [6, 1.0], [7, 1.0], [8, 1.0], [9, 1.0], [10, 1.0], [11, 1.0], [12, 1.0], [13, 1.0], [14, 1.0], [15, 1.0], [16, 1.0], [17, 1.0]])
    output_latency_expected = models.IntegerField(verbose_name="Latency Expected", default=-1)
    input_platform = models.TextField(default=FunPlatform.F1)



class PerformanceBlt(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1_block_size = models.CharField(max_length=20, choices=[(0, "4K"), (1, "8K"), (2, "16K")], verbose_name="Block size")
    input2_mode = models.CharField(max_length=20, choices=[(0, "Read"), (1, "Read-Write")], verbose_name="R/W Mode")
    output1_iops = models.IntegerField(verbose_name="IOPS")
    output2_bw = models.IntegerField(verbose_name="Band-width")
    output3_latency = models.IntegerField(verbose_name="Latency")


class PerformanceIkv(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1_put_value_size = models.IntegerField(verbose_name="PUT Value size", choices=[(0, 4096), (1, 8192)])
    output1_put_per_seccond = models.IntegerField(verbose_name="PUTs per second")


class VolumePerformance(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input_volume = models.TextField(verbose_name="Volume type", choices=[(0, "BLT"), (1, "EC21")])
    input_test = models.TextField(verbose_name="Test type", choices=[(0, "FioSeqWriteSeqReadOnly")])
    input_block_size = models.TextField(verbose_name="Block size", choices=[(0, "4k"), (1, "8k")])
    input_io_depth = models.IntegerField(verbose_name="IO depth", choices=[(0, 1)])
    input_size = models.TextField(verbose_name="Data size", choices=[(0, "4m")])
    input_operation = models.TextField(verbose_name="Operation type", choices=[(0, "read"), (1, "write"), (2, "randread"), (3, "randwrite"), (4, "randrw")])
    output_write_iops = models.IntegerField(verbose_name="Write IOPS")
    output_read_iops = models.IntegerField(verbose_name="Read IOPS")
    output_write_bw = models.IntegerField(verbose_name="Write bandwidth KiB/s")
    output_read_bw = models.IntegerField(verbose_name="Read bandwidth KiB/s")
    output_write_latency = models.IntegerField(verbose_name="Write latency uSecs")
    output_read_latency = models.IntegerField(verbose_name="Read latency uSecs")
    input_platform = models.TextField(default=FunPlatform.F1)

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}".format(self.key,
                                                self.input_volume,
                                                self.input_test,
                                                self.input_block_size,
                                                self.input_size,
                                                self.input_operation,
                                                self.output_write_iops,
                                                self.output_read_iops,
                                                self.output_write_bw,
                                                self.output_write_latency,
                                                self.output_read_latency)


class VolumePerformanceEmulation(models.Model):
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_volume = models.TextField(verbose_name="Volume type", choices=[(0, "BLT"), (1, "EC21")])
    input_test = models.TextField(verbose_name="Test type", choices=[(0, "FioSeqWriteSeqReadOnly")])
    input_block_size = models.TextField(verbose_name="Block size", choices=[(0, "4k"), (1, "8k")])
    input_io_depth = models.IntegerField(verbose_name="IO depth", choices=[(0, 1)])
    input_size = models.TextField(verbose_name="Data size", choices=[(0, "4m")])
    input_operation = models.TextField(verbose_name="Operation type", choices=[(0, "read"), (1, "write"), (2, "randread"), (3, "randwrite"), (4, "randrw")])
    input_fio_job_name = models.TextField(verbose_name="Input FIO job name", default="")
    output_write_iops = models.IntegerField(verbose_name="Write IOPS")
    output_read_iops = models.IntegerField(verbose_name="Read IOPS")
    output_write_bw = models.IntegerField(verbose_name="Write bandwidth KiB/s")
    output_read_bw = models.IntegerField(verbose_name="Read bandwidth KiB/s")
    output_write_latency = models.IntegerField(verbose_name="Write latency uSecs")
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency uSecs", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency uSecs", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency uSecs", default=-1)
    output_read_latency = models.IntegerField(verbose_name="Read latency uSecs")
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency uSecs", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency uSecs", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency uSecs", default=-1)
    input_platform = models.TextField(default=FunPlatform.F1)

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}".format(self.input_date_time,
                                                self.input_volume,
                                                self.input_test,
                                                self.input_block_size,
                                                self.input_size,
                                                self.input_operation,
                                                self.output_write_iops,
                                                self.output_read_iops,
                                                self.output_write_bw,
                                                self.output_write_latency,
                                                self.output_read_latency)


class BltVolumePerformance(models.Model):
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_volume_type = models.TextField(verbose_name="Volume type")
    input_test = models.TextField(verbose_name="Test type")
    input_block_size = models.TextField(verbose_name="Block size")
    input_io_depth = models.IntegerField(verbose_name="IO depth")
    input_io_size = models.TextField(verbose_name="IO size")
    input_operation = models.TextField(verbose_name="Operation type")
    input_num_ssd = models.IntegerField(verbose_name="Number of SSD(s)")
    input_num_volume = models.IntegerField(verbose_name="Number of volume(s)")
    input_fio_job_name = models.TextField(verbose_name="Input FIO job name", default="")
    output_write_iops = models.IntegerField(verbose_name="Write IOPS", default=-1)
    output_read_iops = models.IntegerField(verbose_name="Read IOPS", default=-1)
    output_write_throughput = models.FloatField(verbose_name="Write throughput", default=-1)
    output_read_throughput = models.FloatField(verbose_name="Read throughput", default=-1)
    output_write_avg_latency = models.IntegerField(verbose_name="Write avg latency", default=-1)
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency", default=-1)
    output_write_99_99_latency = models.IntegerField(verbose_name="Write 99.99% latency", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency", default=-1)
    output_read_avg_latency = models.IntegerField(verbose_name="Read avg latency", default=-1)
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency", default=-1)
    output_read_99_99_latency = models.IntegerField(verbose_name="Read 99.99% latency", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency", default=-1)
    output_write_iops_unit = models.TextField(default="ops")
    output_read_iops_unit = models.TextField(default="ops")
    output_write_throughput_unit = models.TextField(default="Mbps")
    output_read_throughput_unit = models.TextField(default="Mbps")
    output_write_avg_latency_unit = models.TextField(default="usecs")
    output_write_90_latency_unit = models.TextField(default="usecs")
    output_write_95_latency_unit = models.TextField(default="usecs")
    output_write_99_99_latency_unit = models.TextField(default="usecs")
    output_write_99_latency_unit = models.TextField(default="usecs")
    output_read_avg_latency_unit = models.TextField(default="usecs")
    output_read_90_latency_unit = models.TextField(default="usecs")
    output_read_95_latency_unit = models.TextField(default="usecs")
    output_read_99_99_latency_unit = models.TextField(default="usecs")
    output_read_99_latency_unit = models.TextField(default="usecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}".format(self.input_date_time,
                                                self.input_volume_type,
                                                self.input_test,
                                                self.input_block_size,
                                                self.input_io_size,
                                                self.input_operation,
                                                self.output_write_iops,
                                                self.output_read_iops,
                                                self.output_write_throughput,
                                                self.output_write_avg_latency,
                                                self.output_read_avg_latency)


class AlibabaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_volume_type = models.TextField(verbose_name="Volume type")
    input_test = models.TextField(verbose_name="Test type")

    input_block_size = models.TextField(verbose_name="Block size")
    input_io_depth = models.IntegerField(verbose_name="IO depth")
    input_io_size = models.TextField(verbose_name="IO size")
    input_operation = models.TextField(verbose_name="Operation type")
    input_num_ssd = models.IntegerField(verbose_name="Number of SSD(s)")
    input_num_volume = models.IntegerField(verbose_name="Number of volume(s)")
    input_num_threads = models.IntegerField(verbose_name="Threads")
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    input_encryption = models.BooleanField(default=False)
    run_time_id = models.IntegerField(default=None, null=True)

    output_write_iops = models.IntegerField(verbose_name="Write IOPS", default=-1)
    output_read_iops = models.IntegerField(verbose_name="Read IOPS", default=-1)
    output_write_throughput = models.FloatField(verbose_name="Write throughput", default=-1)
    output_read_throughput = models.FloatField(verbose_name="Read throughput", default=-1)
    output_write_avg_latency = models.IntegerField(verbose_name="Write avg latency", default=-1)
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency", default=-1)
    output_write_99_99_latency = models.IntegerField(verbose_name="Write 99.99% latency", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency", default=-1)
    output_read_avg_latency = models.IntegerField(verbose_name="Read avg latency", default=-1)
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency", default=-1)
    output_read_99_99_latency = models.IntegerField(verbose_name="Read 99.99% latency", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency", default=-1)

    output_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_write_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_read_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_write_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}".format(self.input_date_time,
                                                self.input_volume_type,
                                                self.input_test,
                                                self.input_block_size,
                                                self.input_io_size,
                                                self.input_operation,
                                                self.output_write_iops,
                                                self.output_read_iops,
                                                self.output_write_throughput,
                                                self.output_write_avg_latency,
                                                self.output_read_avg_latency)


class AlibabaBmvRemoteSsdPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_volume_type = models.TextField(verbose_name="Volume type")
    input_test = models.TextField(verbose_name="Test type")

    input_block_size = models.TextField(verbose_name="Block size")
    input_io_depth = models.IntegerField(verbose_name="IO depth")
    input_io_size = models.TextField(verbose_name="IO size")
    input_operation = models.TextField(verbose_name="Operation type")
    input_num_ssd = models.IntegerField(verbose_name="Number of SSD(s)")
    input_num_volume = models.IntegerField(verbose_name="Number of volume(s)")
    input_num_threads = models.IntegerField(verbose_name="Threads")
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    run_time_id = models.IntegerField(default=None, null=True)

    output_write_iops = models.IntegerField(verbose_name="Write IOPS", default=-1)
    output_read_iops = models.IntegerField(verbose_name="Read IOPS", default=-1)
    output_write_throughput = models.FloatField(verbose_name="Write throughput", default=-1)
    output_read_throughput = models.FloatField(verbose_name="Read throughput", default=-1)
    output_write_avg_latency = models.IntegerField(verbose_name="Write avg latency", default=-1)
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency", default=-1)
    output_write_99_99_latency = models.IntegerField(verbose_name="Write 99.99% latency", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency", default=-1)
    output_read_avg_latency = models.IntegerField(verbose_name="Read avg latency", default=-1)
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency", default=-1)
    output_read_99_99_latency = models.IntegerField(verbose_name="Read 99.99% latency", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency", default=-1)

    output_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_write_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_read_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_write_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)

    def __str__(self):
        return "{}:{}:{}:{}:{}:{}:{}:{}".format(self.input_date_time,
                                                self.input_volume_type,
                                                self.input_test,
                                                self.input_block_size,
                                                self.input_io_size,
                                                self.input_operation,
                                                self.output_write_iops,
                                                self.output_read_iops,
                                                self.output_write_throughput,
                                                self.output_write_avg_latency,
                                                self.output_read_avg_latency)


class InspurZipCompressionRatiosPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_effort_name = models.TextField(default="")
    input_corpus_name = models.TextField(default="")
    output_f1_compression_ratio = models.FloatField(verbose_name="F1 Compression Ratio", default=-1)
    output_f1_compression_ratio_unit = models.TextField(default="number")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return str(self.__dict__)


class AllocSpeedPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_app = models.TextField(verbose_name="alloc_speed_test", default="alloc_speed_test",  choices=[(0, "alloc_speed_test")])
    output_one_malloc_free_wu = models.IntegerField(verbose_name="Time in ns (WU)")
    output_one_malloc_free_wu_unit = models.TextField(default="nsecs")
    output_one_malloc_free_threaded = models.IntegerField(verbose_name="Time in ns (Threaded)")
    output_one_malloc_free_threaded_unit = models.TextField(default="nsecs")
    output_one_malloc_free_classic_min = models.IntegerField(default=-1, verbose_name="Time in ns (Classic): Min")
    output_one_malloc_free_classic_min_unit = models.TextField(default="nsecs")
    output_one_malloc_free_classic_avg = models.IntegerField(default=-1, verbose_name="Time in ns (Classic): Avg")
    output_one_malloc_free_classic_avg_unit = models.TextField(default="nsecs")
    output_one_malloc_free_classic_max = models.IntegerField(default=-1, verbose_name="Time in ns (Classic): Max")
    output_one_malloc_free_classic_max_unit = models.TextField(default="nsecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}..{}..{}..{}..{}..{}..{}".format(self.key, self.output_one_malloc_free_wu, self.output_one_malloc_free_threaded,
                                       self.output_one_malloc_free_classic_min, self.output_one_malloc_free_classic_avg,
                                       self.output_one_malloc_free_classic_max, self.input_date_time)


class WuLatencyAllocStack(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_app = models.TextField(verbose_name="wu_latency_test: alloc_stack", default="wu_latency_test", choices=[(0, "wu_latency_test")])
    output_min = models.IntegerField(verbose_name="Min (ns)")
    output_min_unit = models.TextField(default="nsecs")
    output_max = models.IntegerField(verbose_name="Max (ns)")
    output_max_unit = models.TextField(default="nsecs")
    output_avg = models.IntegerField(verbose_name="Avg (ns)")
    output_avg_unit = models.TextField(default="nsecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}..{}..{}..{}".format(self.key, self.output_min, self.output_avg, self.output_max)

class WuLatencyUngated(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.TextField(verbose_name="wu_latency_test: Ungated WU", default="wu_latency_test", choices=[(0, "wu_latency_test")])
    output_min = models.IntegerField(verbose_name="Min (ns)")
    output_min_unit = models.TextField(default="nsecs")
    output_max = models.IntegerField(verbose_name="Max (ns)")
    output_max_unit = models.TextField(default="nsecs")
    output_avg = models.IntegerField(verbose_name="Avg (ns)")
    output_avg_unit = models.TextField(default="nsecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}..{}..{}..{}".format(self.key, self.output_min, self.output_avg, self.output_max)

class VolumePerformanceSerializer(ModelSerializer):
    class Meta:
        model = VolumePerformance
        fields = "__all__"


class AllocSpeedPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()
    class Meta:
        model = AllocSpeedPerformance
        fields = "__all__"

class UnitTestPerformance(models.Model):
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=20, default="unit_tests", choices=[(0, "unit_tests")])
    input_job_id = models.IntegerField(verbose_name="Job Id", default=0)
    output_num_passed = models.IntegerField(verbose_name="Passed")
    output_num_failed = models.IntegerField(verbose_name="Failed")
    output_num_disabled = models.IntegerField(verbose_name="Disabled")
    input_hardware_version = models.CharField(max_length=50, default="", verbose_name="Hardware version")
    input_software_date = models.CharField(max_length=50, default="", verbose_name="Software date")
    input_git_commit = models.CharField(max_length=100, default="", verbose_name="Git commit")
    input_branch_funsdk = models.CharField(max_length=100, default="", verbose_name="Branch FunSDK")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}..{}..{}".format(self.input_software_date, self.output_num_passed, self.output_num_failed)

class UnitTestPerformanceSerializer(ModelSerializer):
    class Meta:
        model = UnitTestPerformance
        fields = "__all__"

class GenericSerializer(ModelSerializer):
    def set_model(self, model):
        pass

class EcPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_ndata_min = models.IntegerField(verbose_name="ndata min", default=8)
    input_ndata_max = models.IntegerField(verbose_name="ndata min", default=8)
    input_nparity_min = models.IntegerField(verbose_name="nparity min", default=4)
    input_stridelen_min = models.IntegerField(verbose_name="strideline min", default=4096)
    input_stridelen_max = models.IntegerField(verbose_name="strideline max", default=4096)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    output_encode_latency_min = models.IntegerField(verbose_name="Encode Latency min")
    output_encode_latency_min_unit = models.TextField(default="nsecs")
    output_encode_latency_max = models.IntegerField(verbose_name="Encode Latency max")
    output_encode_latency_max_unit = models.TextField(default="nsecs")
    output_encode_latency_avg = models.IntegerField(verbose_name="Encode Latency avg")
    output_encode_latency_avg_unit = models.TextField(default="nsecs")

    output_encode_throughput_min = models.IntegerField(verbose_name="Encode Throughput min")
    output_encode_throughput_min_unit = models.TextField(default="Gbps")
    output_encode_throughput_max = models.IntegerField(verbose_name="Encode Throughput max")
    output_encode_throughput_max_unit = models.TextField(default="Gbps")
    output_encode_throughput_avg = models.IntegerField(verbose_name="Encode Throughput avg")
    output_encode_throughput_avg_unit = models.TextField(default="Gbps")

    output_recovery_latency_min = models.IntegerField(verbose_name="Recovery Latency min")
    output_recovery_latency_min_unit = models.TextField(default="nsecs")
    output_recovery_latency_max = models.IntegerField(verbose_name="Recovery Latency max")
    output_recovery_latency_max_unit = models.TextField(default="nsecs")
    output_recovery_latency_avg = models.IntegerField(verbose_name="Recovery Latency avg")
    output_recovery_latency_avg_unit = models.TextField(default="nsecs")

    output_recovery_throughput_min = models.IntegerField(verbose_name="Recovery Throughput min")
    output_recovery_throughput_min_unit = models.TextField(default="Gbps")
    output_recovery_throughput_max = models.IntegerField(verbose_name="Recovery Throughput max")
    output_recovery_throughput_max_unit = models.TextField(default="Gbps")
    output_recovery_throughput_avg = models.IntegerField(verbose_name="Recovery Throughput avg")
    output_recovery_throughput_avg_unit = models.TextField(default="Gbps")

    def __str__(self):
        return str(self.__dict__)


class BcopyPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_iterations = models.IntegerField(verbose_name="Iterations", default=10)
    input_coherent = models.TextField(verbose_name="Coherent/Non", default="Coherent", choices=[(0, "Coherent"), (1, "Non-coherent")])
    input_plain = models.TextField(verbose_name="Plain/DMA", default="Plain", choices=[(0, "Plain"), (1, "DMA")])
    input_size = models.IntegerField(verbose_name="Size in KB", choices=[(0, "4"), (1, "8"), (2, "16"), (3, "32"), (4, "64")])
    run_time_id = models.IntegerField(default=None, null=True)

    output_latency_units = models.TextField(verbose_name="Latency units")
    output_latency_min = models.IntegerField(verbose_name="Latency min")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_max = models.IntegerField(verbose_name="Latency max")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_latency_avg = models.IntegerField(verbose_name="Latency max")
    output_latency_avg_unit = models.TextField(default="nsecs")
    input_latency_perf_name = models.TextField(verbose_name="Latency perf name")
    output_average_bandwith = models.IntegerField(verbose_name="Average Bandwidth in Gbps")
    output_average_bandwith_unit = models.TextField(default="Gbps")
    input_average_bandwith_perf_name = models.TextField(verbose_name="Average Bandwidth perf name")
    input_platform = models.TextField(default=FunPlatform.F1)

    def __str__(self):
        return str(self.__dict__)


class BcopyFloodDmaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_n = models.IntegerField(verbose_name="N", default=0, choices=[(0, "1"), (1, "2"), (2, "4"), (3, "8"), (4, "16"), (5, "32"), (6, "64")])
    input_size = models.IntegerField(verbose_name="Size in KB", choices=[(0, "4"), (1, "8"), (2, "16"), (3, "32"), (4, "64")])
    output_latency_units = models.TextField(verbose_name="Latency units")
    output_latency_min = models.IntegerField(verbose_name="Latency min")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_max = models.IntegerField(verbose_name="Latency max")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_latency_avg = models.IntegerField(verbose_name="Latency avg")
    output_latency_avg_unit = models.TextField(default="nsecs")
    input_latency_perf_name = models.TextField(verbose_name="Latency perf name")
    output_average_bandwith = models.IntegerField(verbose_name="Average Bandwidth in Gbps")
    output_average_bandwith_unit = models.TextField(default="Gbps")
    input_average_bandwith_perf_name = models.TextField(verbose_name="Average Bandwidth perf name")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return str(self.__dict__)


class EcVolPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=20, default="voltest", choices=[(0, "voltest")])
    output_ecvol_ec_stats_latency_ns_max = models.IntegerField(verbose_name="Latency max", default=-1)
    output_ecvol_ec_stats_latency_ns_max_unit = models.TextField(default="nsecs")
    output_ecvol_ec_stats_latency_ns_avg = models.IntegerField(verbose_name="Latency avg", default=-1)
    output_ecvol_ec_stats_latency_ns_avg_unit = models.TextField(default="nsecs")
    output_ecvol_ec_stats_latency_ns_min = models.IntegerField(verbose_name="Latency min", default=-1)
    output_ecvol_ec_stats_latency_ns_min_unit = models.TextField(default="nsecs")
    output_ecvol_ec_stats_iops = models.IntegerField(verbose_name="IOPS", default=-1)
    output_ecvol_ec_stats_iops_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)


class LsvZipCryptoPerformance(models.Model):
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=20, default="lsv_test", choices=[(0, "lsv_test")])
    output_filter_type_xts_encrypt_latency_ns_max = models.IntegerField(verbose_name="Enc: Latency max", default=-1)
    output_filter_type_xts_encrypt_latency_ns_avg = models.IntegerField(verbose_name="Enc: Latency avg", default=-1)
    output_filter_type_xts_encrypt_latency_ns_min = models.IntegerField(verbose_name="Enc: Latency min", default=-1)
    output_filter_type_xts_encrypt_iops = models.IntegerField(verbose_name="Enc: IOPS", default=-1)
    output_filter_type_xts_encrypt_avg_op_bw_mbps = models.IntegerField(verbose_name="Enc: BW avg", default=-1)
    output_filter_type_xts_encrypt_total_op_bw_mbps = models.IntegerField(verbose_name="Enc: BW total", default=-1)
    output_filter_type_xts_decrypt_latency_ns_max = models.IntegerField(verbose_name="Dec: Latency max", default=-1)
    output_filter_type_xts_decrypt_latency_ns_avg = models.IntegerField(verbose_name="Dec: Latency avg", default=-1)
    output_filter_type_xts_decrypt_latency_ns_min = models.IntegerField(verbose_name="Dec: Latency min", default=-1)
    output_filter_type_xts_decrypt_iops = models.IntegerField(verbose_name="Dec: IOPS", default=-1)
    output_filter_type_xts_decrypt_avg_op_bw_mbps = models.IntegerField(verbose_name="Dec: BW avg", default=-1)
    output_filter_type_xts_decrypt_total_op_bw_mbps = models.IntegerField(verbose_name="Dec: Total BW", default=-1)
    output_filter_type_deflate_latency_ns_max = models.IntegerField(verbose_name="Deflate: Latency max", default=-1)
    output_filter_type_deflate_latency_ns_avg = models.IntegerField(verbose_name="Deflate: Latency avg", default=-1)
    output_filter_type_deflate_latency_ns_min = models.IntegerField(verbose_name="Deflate: Latency min", default=-1)
    output_filter_type_deflate_iops = models.IntegerField(verbose_name="Deflate: IOPS", default=-1)
    output_filter_type_deflate_avg_op_bw_mbps = models.IntegerField(verbose_name="Deflate: BW avg", default=-1)
    output_filter_type_deflate_total_op_bw_mbps = models.IntegerField(verbose_name="Deflate: BW total", default=-1)
    output_filter_type_inflate_latency_ns_max = models.IntegerField(verbose_name="Inflate: Latency max", default=-1)
    output_filter_type_inflate_latency_ns_avg = models.IntegerField(verbose_name="Inflate: Latency avg", default=-1)
    output_filter_type_inflate_latency_ns_min = models.IntegerField(verbose_name="Inflate: Latency min", default=-1)
    output_filter_type_inflate_iops = models.IntegerField(verbose_name="Inflate: IOPS", default=-1)
    output_filter_type_inflate_avg_op_bw_mbps = models.IntegerField(verbose_name="Inflate: BW avg", default=-1)
    output_filter_type_inflate_total_op_bw_mbps = models.IntegerField(verbose_name="Inflate: BW total ", default=-1)
    output_lsv_read_latency_ns_max = models.IntegerField(verbose_name="LSV read: Latency max", default=-1)
    output_lsv_read_latency_ns_avg = models.IntegerField(verbose_name="LSV read: Latency avg", default=-1)
    output_lsv_read_latency_ns_min = models.IntegerField(verbose_name="LSV read: Latency min", default=-1)
    output_lsv_read_iops = models.IntegerField(verbose_name="LSV read: IOPS", default=-1)
    output_lsv_read_avg_op_bw_mbps = models.IntegerField(verbose_name="LSV read: BW avg", default=-1)
    output_lsv_read_total_op_bw_mbps = models.IntegerField(verbose_name="LSV read: BW total", default=-1)
    output_lsv_write_latency_ns_max = models.IntegerField(verbose_name="LSV write: Latency max", default=-1)
    output_lsv_write_latency_ns_avg = models.IntegerField(verbose_name="LSV write: Latency avg", default=-1)
    output_lsv_write_latency_ns_min = models.IntegerField(verbose_name="LSV write: Latency min", default=-1)
    output_lsv_write_iops = models.IntegerField(verbose_name="LSV write: IOPS", default=-1)
    output_lsv_write_avg_op_bw_mbps = models.IntegerField(verbose_name="LSV write: BW avg", default=-1)
    output_lsv_write_total_op_bw_mbps = models.IntegerField(verbose_name="LSV write: BW total", default=-1)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class NuTransitPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.IntegerField(verbose_name="Fixed Frame Size Test", choices=[(0, 1500), (1, 1000), (2, 200), (3, 9000), (4, 16380), (5, 64)])
    output_throughput = models.FloatField(verbose_name="Throughput in Gbps")
    output_latency_avg = models.FloatField(verbose_name="Latency Avg in us")
    output_latency_max = models.FloatField(verbose_name="Latency Max in us")
    output_latency_min = models.FloatField(verbose_name="Latency Min in us")
    output_latency_P99 = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90 = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50 = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min = models.FloatField(verbose_name="Jitter min in us", default=0)
    output_jitter_max = models.FloatField(verbose_name="Jitter max in us", default=0)
    output_jitter_avg = models.FloatField(verbose_name="Jitter avg in us", default=0)
    output_pps = models.FloatField(verbose_name="Packets per sec", default=0)
    output_throughput_unit = models.TextField(default="Gbps")
    output_latency_avg_unit = models.TextField(default="usecs")
    output_latency_max_unit = models.TextField(default="usecs")
    output_latency_min_unit = models.TextField(default="usecs")
    output_latency_P99_unit = models.TextField(default="usecs")
    output_latency_P90_unit = models.TextField(default="usecs")
    output_latency_P50_unit = models.TextField(default="usecs")
    output_jitter_min_unit = models.TextField(default="usecs")
    output_jitter_max_unit = models.TextField(default="usecs")
    output_jitter_avg_unit = models.TextField(default="usecs")
    output_pps_unit = models.TextField(default="Mpps")
    input_mode = models.CharField(verbose_name="Port modes (25, 50 or 100 G)", max_length=20, default="")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=1000000)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="UDP")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class HuThroughputPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.IntegerField(verbose_name="Frame Size")
    output_throughput_h2n = models.FloatField(verbose_name="Throughput in Gbps", default=-1)
    output_throughput_n2h = models.FloatField(verbose_name="Throughput in Gbps", default=-1)
    output_throughput_h2h = models.FloatField(verbose_name="Throughput in Gbps", default=-1)
    output_pps_h2n = models.FloatField(verbose_name="Packets per sec", default=-1)
    output_pps_n2h = models.FloatField(verbose_name="Packets per sec", default=-1)
    output_pps_h2h = models.FloatField(verbose_name="Packets per sec", default=-1)
    output_throughput_h2n_unit = models.TextField(default="Gbps")
    output_throughput_n2h_unit = models.TextField(default="Gbps")
    output_throughput_h2h_unit = models.TextField(default="Gbps")
    output_pps_h2n_unit = models.TextField(default="Mpps")
    output_pps_n2h_unit = models.TextField(default="Mpps")
    output_pps_h2h_unit = models.TextField(default="Mpps")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=1)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="TCP")
    input_num_hosts = models.IntegerField(verbose_name="Number of Hosts", default=1)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class HuLatencyPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.IntegerField(verbose_name="Frame Size")
    output_latency_avg_h2n = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_h2n = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_h2n = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_h2n = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_h2n = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_h2n = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_h2n = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_h2n = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_h2n = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_n2h = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_n2h = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_n2h = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_n2h = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_n2h = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_n2h = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_n2h = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_n2h = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_n2h = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_h2h = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_h2h = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_h2h = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_h2h = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_h2h = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_h2h = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_h2h = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_h2h = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_h2h = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_h2n_unit = models.TextField(default="usecs")
    output_latency_max_h2n_unit = models.TextField(default="usecs")
    output_latency_min_h2n_unit = models.TextField(default="usecs")
    output_latency_P99_h2n_unit = models.TextField(default="usecs")
    output_latency_P90_h2n_unit = models.TextField(default="usecs")
    output_latency_P50_h2n_unit = models.TextField(default="usecs")
    output_jitter_min_h2n_unit = models.TextField(default="usecs")
    output_jitter_max_h2n_unit = models.TextField(default="usecs")
    output_jitter_avg_h2n_unit = models.TextField(default="usecs")
    output_latency_avg_n2h_unit = models.TextField(default="usecs")
    output_latency_max_n2h_unit = models.TextField(default="usecs")
    output_latency_min_n2h_unit = models.TextField(default="usecs")
    output_latency_P99_n2h_unit = models.TextField(default="usecs")
    output_latency_P90_n2h_unit = models.TextField(default="usecs")
    output_latency_P50_n2h_unit = models.TextField(default="usecs")
    output_jitter_min_n2h_unit = models.TextField(default="usecs")
    output_jitter_max_n2h_unit = models.TextField(default="usecs")
    output_jitter_avg_n2h_unit = models.TextField(default="usecs")
    output_latency_avg_h2h_unit = models.TextField(default="usecs")
    output_latency_max_h2h_unit = models.TextField(default="usecs")
    output_latency_min_h2h_unit = models.TextField(default="usecs")
    output_latency_P99_h2h_unit = models.TextField(default="usecs")
    output_latency_P90_h2h_unit = models.TextField(default="usecs")
    output_latency_P50_h2h_unit = models.TextField(default="usecs")
    output_jitter_min_h2h_unit = models.TextField(default="usecs")
    output_jitter_max_h2h_unit = models.TextField(default="usecs")
    output_jitter_avg_h2h_unit = models.TextField(default="usecs")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=1)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="TCP")
    input_num_hosts = models.IntegerField(verbose_name="Number of Hosts", default=1)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class HuLatencyUnderLoadPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.IntegerField(verbose_name="Frame Size")
    output_latency_avg_uload_h2n = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_uload_h2n = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_uload_h2n = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_uload_h2n = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_uload_h2n = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_uload_h2n = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_uload_h2n = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_uload_h2n = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_uload_h2n = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_uload_n2h = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_uload_n2h = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_uload_n2h = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_uload_n2h = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_uload_n2h = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_uload_n2h = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_uload_n2h = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_uload_n2h = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_uload_n2h = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_uload_h2h = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max_uload_h2h = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min_uload_h2h = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_latency_P99_uload_h2h = models.FloatField(verbose_name="Tail Latency in us", default=-1)
    output_latency_P90_uload_h2h = models.FloatField(verbose_name="P90 Latency in us", default=-1)
    output_latency_P50_uload_h2h = models.FloatField(verbose_name="P50 Latency in us", default=-1)
    output_jitter_min_uload_h2h = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max_uload_h2h = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg_uload_h2h = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_latency_avg_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_max_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_min_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_P99_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_P90_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_P50_uload_h2n_unit = models.TextField(default="usecs")
    output_jitter_min_uload_h2n_unit = models.TextField(default="usecs")
    output_jitter_max_uload_h2n_unit = models.TextField(default="usecs")
    output_jitter_avg_uload_h2n_unit = models.TextField(default="usecs")
    output_latency_avg_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_max_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_min_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_P99_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_P90_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_P50_uload_n2h_unit = models.TextField(default="usecs")
    output_jitter_min_uload_n2h_unit = models.TextField(default="usecs")
    output_jitter_max_uload_n2h_unit = models.TextField(default="usecs")
    output_jitter_avg_uload_n2h_unit = models.TextField(default="usecs")
    output_latency_avg_uload_h2h_unit = models.TextField(default="usecs")
    output_latency_max_uload_h2h_unit = models.TextField(default="usecs")
    output_latency_min_uload_h2h_unit = models.TextField(default="usecs")
    output_latency_P99_uload_h2h_unit = models.TextField(default="usecs")
    output_latency_P90_uload_h2h_unit = models.TextField(default="usecs")
    output_latency_P50_uload_h2h_unit = models.TextField(default="usecs")
    output_jitter_min_uload_h2h_unit = models.TextField(default="usecs")
    output_jitter_max_uload_h2h_unit = models.TextField(default="usecs")
    output_jitter_avg_uload_h2h_unit = models.TextField(default="usecs")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=1)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="TCP")
    input_num_hosts = models.IntegerField(verbose_name="Number of Hosts", default=1)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class TeraMarkJuniperNetworkingPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.FloatField(verbose_name="Frame Size", default=-1)
    output_throughput = models.FloatField(verbose_name="Throughput in Gbps", default=-1)
    output_latency_avg = models.FloatField(verbose_name="Latency Avg in us", default=-1)
    output_latency_max = models.FloatField(verbose_name="Latency Max in us", default=-1)
    output_latency_min = models.FloatField(verbose_name="Latency Min in us", default=-1)
    output_jitter_min = models.FloatField(verbose_name="Jitter min in us", default=-1)
    output_jitter_max = models.FloatField(verbose_name="Jitter max in us", default=-1)
    output_jitter_avg = models.FloatField(verbose_name="Jitter avg in us", default=-1)
    output_pps = models.FloatField(verbose_name="Packets per sec", default=-1)
    output_throughput_unit = models.TextField(default="Gbps")
    output_latency_avg_unit = models.TextField(default="usecs")
    output_latency_max_unit = models.TextField(default="usecs")
    output_latency_min_unit = models.TextField(default="usecs")
    output_jitter_min_unit = models.TextField(default="usecs")
    output_jitter_max_unit = models.TextField(default="usecs")
    output_jitter_avg_unit = models.TextField(default="usecs")
    output_pps_unit = models.TextField(default="Mpps")
    input_mode = models.CharField(verbose_name="Port modes (25, 50 or 100 G)", max_length=20, default="")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=0)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="UDP")
    input_half_load_latency = models.BooleanField(default=False)
    input_memory = models.TextField(default="HBM")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class TeraMarkFunTcpThroughputPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.FloatField(verbose_name="Frame Size")
    input_mode = models.CharField(verbose_name="Port modes", max_length=20, default="")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_num_flows = models.IntegerField(verbose_name="Number of flows", default=1)
    output_throughput = models.FloatField(verbose_name="Throughput in Gbps")
    output_pps = models.FloatField(verbose_name="Packets per sec")
    output_throughput_unit = models.TextField(default="Gbps")
    output_pps_unit = models.TextField(default="Mpps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)


    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkFunTcpConnectionsPerSecondPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.FloatField(verbose_name="Frame Size")
    output_max_latency = models.FloatField(verbose_name="Max Latency", default=-1)
    output_max_cps = models.IntegerField(verbose_name="Max CPS", default=-1)
    output_avg_latency = models.FloatField(verbose_name="Avg Latency", default=-1)
    output_max_latency_unit = models.TextField(default="usecs")
    output_avg_latency_unit = models.TextField(default="usecs")
    output_max_cps_unit = models.TextField(default="cps")
    input_mode = models.CharField(verbose_name="Port modes", max_length=20, default="")
    input_version = models.CharField(verbose_name="Version", max_length=50)
    input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
    input_cps_type = models.TextField(verbose_name="CPS Type", default="")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s
#
# class TeraMarkFunTcpConcurrentConnectionsPerformance(models.Model):
#     status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
#     input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
#     input_frame_size = models.FloatField(verbose_name="Frame Size")
#     output_throughput = models.FloatField(verbose_name="Throughput in Gbps")
#     output_latency_avg = models.FloatField(verbose_name="Latency Avg in us")
#     output_latency_max = models.FloatField(verbose_name="Latency Max in us")
#     output_latency_min = models.FloatField(verbose_name="Latency Min in us")
#     output_jitter_min = models.FloatField(verbose_name="Jitter min in us")
#     output_jitter_max = models.FloatField(verbose_name="Jitter max in us")
#     output_jitter_avg = models.FloatField(verbose_name="Jitter avg in us")
#     output_pps = models.FloatField(verbose_name="Packets per sec")
#     output_throughput_unit = models.TextField(default="Gbps")
#     output_latency_avg_unit = models.TextField(default="usecs")
#     output_latency_max_unit = models.TextField(default="usecs")
#     output_latency_min_unit = models.TextField(default="usecs")
#     output_jitter_min_unit = models.TextField(default="usecs")
#     output_jitter_max_unit = models.TextField(default="usecs")
#     output_jitter_avg_unit = models.TextField(default="usecs")
#     output_pps_unit = models.TextField(default="Mpps")
#     input_mode = models.CharField(verbose_name="Port modes (25, 50 or 100 G)", max_length=20, default="")
#     input_version = models.CharField(verbose_name="Version", max_length=50)
#     input_flow_type = models.CharField(verbose_name="Flow Type", max_length=50, default="")
#     input_number_flows = models.IntegerField(verbose_name="Number of flows", default=0)
#     input_offloads = models.BooleanField(default=False)
#     input_protocol = models.TextField(default="UDP")
#
#     def __str__(self):
#         s = ""
#         for key, value in self.__dict__.iteritems():
#             s += "{}:{} ".format(key, value)
#         return s

class VoltestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=20, default="voltest", choices=[(0, "voltest")])
    output_VOL_TYPE_BLK_LSV_write_latency_max = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_latency_max", default=-1)
    output_VOL_TYPE_BLK_LSV_write_latency_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_latency_avg", default=-1)
    output_VOL_TYPE_BLK_LSV_write_latency_min = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_latency_min", default=-1)
    output_VOL_TYPE_BLK_LSV_write_IOPS = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_IOPS", default=-1)
    output_VOL_TYPE_BLK_LSV_write_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_Bandwidth_avg", default=-1)
    output_VOL_TYPE_BLK_LSV_write_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_write_Bandwidth_total", default=-1)
    output_VOL_TYPE_BLK_LSV_read_latency_max = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_latency_max", default=-1)
    output_VOL_TYPE_BLK_LSV_read_latency_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_latency_avg", default=-1)
    output_VOL_TYPE_BLK_LSV_read_latency_min = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_latency_min", default=-1)
    output_VOL_TYPE_BLK_LSV_read_IOPS = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_IOPS", default=-1)
    output_VOL_TYPE_BLK_LSV_read_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_Bandwidth_avg", default=-1)
    output_VOL_TYPE_BLK_LSV_read_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_LSV_read_Bandwidth_total", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_latency_max = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_latency_max", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_latency_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_latency_avg", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_latency_min = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_latency_min", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_IOPS = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_IOPS", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_avg", default=-1)
    output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_total = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_total", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_latency_max = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_latency_max", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_latency_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_latency_avg", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_latency_min = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_latency_min", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_IOPS = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_IOPS", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_avg", default=-1)
    output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_total = models.IntegerField(verbose_name="output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_total", default=-1)
    output_FILTER_TYPE_DEFLATE_latency_max = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_latency_max", default=-1)
    output_FILTER_TYPE_DEFLATE_latency_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_latency_avg", default=-1)
    output_FILTER_TYPE_DEFLATE_latency_min = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_latency_min", default=-1)
    output_FILTER_TYPE_DEFLATE_IOPS = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_IOPS", default=-1)
    output_FILTER_TYPE_DEFLATE_Bandwidth_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_Bandwidth avg", default=-1)
    output_FILTER_TYPE_DEFLATE_Bandwidth_total = models.IntegerField(verbose_name="output_FILTER_TYPE_DEFLATE_Bandwidth total", default=-1)
    output_FILTER_TYPE_INFLATE_latency_max = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_latency_max", default=-1)
    output_FILTER_TYPE_INFLATE_latency_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_latency_avg", default=-1)
    output_FILTER_TYPE_INFLATE_latency_min = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_latency_min", default=-1)
    output_FILTER_TYPE_INFLATE_IOPS = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_IOPS", default=-1)
    output_FILTER_TYPE_INFLATE_Bandwidth_avg = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_Bandwidth avg", default=-1)
    output_FILTER_TYPE_INFLATE_Bandwidth_total = models.IntegerField(verbose_name="output_FILTER_TYPE_INFLATE_Bandwidth total", default=-1)
    output_VOL_TYPE_BLK_EC_write_latency_max = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_latency_max", default=-1)
    output_VOL_TYPE_BLK_EC_write_latency_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_latency_avg", default=-1)
    output_VOL_TYPE_BLK_EC_write_latency_min = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_latency_min", default=-1)
    output_VOL_TYPE_BLK_EC_write_IOPS = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_IOPS", default=-1)
    output_VOL_TYPE_BLK_EC_write_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_Bandwidth_avg", default=-1)
    output_VOL_TYPE_BLK_EC_write_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_Bandwidth_total", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_max = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_max", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_avg", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_min = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_min", default=-1)
    output_VOL_TYPE_BLK_EC_read_IOPS = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_IOPS", default=-1)
    output_VOL_TYPE_BLK_EC_read_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_Bandwidth avg", default=-1)
    output_VOL_TYPE_BLK_EC_read_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_Bandwidth total", default=-1)
    output_VOL_TYPE_BLK_LSV_write_latency_max_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_write_latency_avg_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_write_latency_min_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_write_IOPS_unit = models.TextField(default="ops")
    output_VOL_TYPE_BLK_LSV_write_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_LSV_write_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_LSV_read_latency_max_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_read_latency_avg_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_read_latency_min_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_LSV_read_IOPS_unit = models.TextField(default="ops")
    output_VOL_TYPE_BLK_LSV_read_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_LSV_read_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_XTS_ENCRYPT_latency_max_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_ENCRYPT_latency_avg_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_ENCRYPT_latency_min_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_ENCRYPT_IOPS_unit = models.TextField(default="ops")
    output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_XTS_ENCRYPT_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_XTS_DECRYPT_latency_max_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_DECRYPT_latency_avg_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_DECRYPT_latency_min_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_XTS_DECRYPT_IOPS_unit = models.TextField(default="ops")
    output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_XTS_DECRYPT_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_DEFLATE_latency_max_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_DEFLATE_latency_avg_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_DEFLATE_latency_min_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_DEFLATE_IOPS_unit = models.TextField(default="ops")
    output_FILTER_TYPE_DEFLATE_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_DEFLATE_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_INFLATE_latency_max_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_INFLATE_latency_avg_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_INFLATE_latency_min_unit = models.TextField(default="nsecs")
    output_FILTER_TYPE_INFLATE_IOPS_unit = models.TextField(default="ops")
    output_FILTER_TYPE_INFLATE_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_FILTER_TYPE_INFLATE_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_EC_write_latency_max_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_write_latency_avg_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_write_latency_min_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_write_IOPS_unit = models.TextField(default="ops")
    output_VOL_TYPE_BLK_EC_write_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_EC_write_Bandwidth_total_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_EC_read_latency_max_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_read_latency_avg_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_read_latency_min_unit = models.TextField(default="nsecs")
    output_VOL_TYPE_BLK_EC_read_IOPS_unit = models.TextField(default="ops")
    output_VOL_TYPE_BLK_EC_read_Bandwidth_avg_unit = models.TextField(default="Mbps")
    output_VOL_TYPE_BLK_EC_read_Bandwidth_total_unit = models.TextField(default="Mbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return "{}: {}".format(self.input_date_time, self.output_VOL_TYPE_BLK_LSV_write_Bandwidth_total)

class WuDispatchTestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="dispatch_speed_test", choices=[(0, "dispatch_speed_test")])
    input_metric_name = models.CharField(max_length=30, default="wu_dispatch_latency_cycles", choices=[(0, "wu_dispatch_latency_cycles")])
    output_average = models.IntegerField(verbose_name="Output WU Dispatch Performanmce Test Average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class WuSendSpeedTestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="wu_send_speed_test", choices=[(0, "wu_send_speed_test")])
    input_metric_name = models.CharField(max_length=40, default="wu_send_ungated_latency_cycles", choices=[(0, "wu_send_ungated_latency_cycles")])
    output_average = models.IntegerField(verbose_name="Output WU Send Speed Performanmce Test Average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakFunMallocPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="soak_malloc_fun_malloc", choices=[(0, "soak_malloc_fun_malloc")])
    input_metric_name = models.CharField(max_length=40, default="soak_two_fun_malloc_fun_free", choices=[(0, "soak_two_fun_malloc_fun_free")])
    output_ops_per_sec = models.IntegerField(verbose_name="Soak Fun Malloc Test ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakClassicMallocPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="soak_malloc_classic", choices=[(0, "soak_malloc_classic")])
    input_metric_name = models.CharField(max_length=40, default="soak_two_classic_malloc_free", choices=[(0, "soak_two_classic_malloc_free")])
    output_ops_per_sec = models.IntegerField(verbose_name="Soak Classic Malloc Test ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeRsaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_rsa_crt_dec_no_pad_soak", choices=[(0, "pke_rsa_crt_dec_no_pad_soak")])
    input_metric_name = models.CharField(max_length=40, default="RSA_CRT_2048_decryptions", choices=[(0, "RSA_CRT_2048_decryptions")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeRsa4kPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=50, default="pke_rsa_crt_dec_no_pad_4096_soak", choices=[(0, "pke_rsa_crt_dec_no_pad_4096_soak")])
    input_metric_name = models.CharField(max_length=40, default="RSA_CRT_4096_decryptions", choices=[(0, "RSA_CRT_4096_decryptions")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeEcdh256Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_ecdh_soak_256", choices=[(0, "pke_ecdh_soak_256")])
    input_metric_name = models.CharField(max_length=40, default="ECDH_P256", choices=[(0, "ECDH_P256")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeEcdh25519Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_ecdh_soak_25519", choices=[(0, "pke_ecdh_soak_25519")])
    input_metric_name = models.CharField(max_length=40, default="ECDH_25519", choices=[(0, "ECDH_25519")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PkeX25519TlsSoakPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_x25519_2k_tls_soak", choices=[(0, "pke_x25519_2k_tls_soak")])
    input_metric_name = models.CharField(max_length=40, default="ECDHE_RSA X25519 RSA 2K", choices=[(0, "ECDHE_RSA X25519 RSA 2K")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops/sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PkeP256TlsSoakPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_p256_2k_tls_soak", choices=[(0, "pke_p256_2k_tls_soak")])
    input_metric_name = models.CharField(max_length=40, default="ECDHE_RSA P256 RSA 2K", choices=[(0, "ECDHE_RSA P256 RSA 2K")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops/sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakDmaMemcpyCoherentPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakDmaMemcpyNonCoherentPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class SoakDmaMemcpyThresholdPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_threshold_unit = models.TextField(default="KB")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_threshold = models.FloatField(verbose_name="Threshold", default=-1)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class SoakDmaMemsetPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    input_coherent = models.BooleanField(default=True)
    input_buffer_memory = models.BooleanField(default=False)
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class ChannelParallPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_number_channels = models.BigIntegerField(default=-1)
    input_busy_loop_usecs = models.IntegerField(default=-1)
    input_data_pool_count = models.IntegerField(default=-1)
    input_metric_name = models.TextField(default="")
    output_channel_parall_speed = models.BigIntegerField(default=-1)
    output_channel_parall_speed_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class TeraMarkCryptoPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="crypto_api_perf")
    input_algorithm = models.CharField(max_length=30, default="")
    input_operation = models.CharField(max_length=30, default="")
    input_pkt_size = models.IntegerField(verbose_name="bytes", default=-1)
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_latency_min = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_avg = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_max = models.IntegerField(verbose_name="ns", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    output_throughput_unit = models.TextField(default="Gbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperCryptoTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="crypto_dp_tunnel")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperIpsecEncryptionSingleTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="ipsec_tunnel_throughput")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperIpsecEncryptionMultiTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="ipsec_tunnel_throughput")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperIpsecDecryptionSingleTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="ipsec_tunnel_throughput")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperIpsecDecryptionMultiTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="ipsec_tunnel_throughput")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class JuniperTlsTunnelPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.TextField(default="crypto_dp_tunnel")
    input_num_tunnels = models.IntegerField(default=-1)
    input_algorithm = models.TextField(default="")
    input_operation = models.TextField(default="")
    input_key_size = models.IntegerField(default=-1)
    input_src_memory = models.TextField(default="BM")
    input_dst_memory = models.TextField(default="BM")
    input_pkt_size = models.FloatField(verbose_name="pkt size B", default=-1)
    output_packets_per_sec = models.FloatField(verbose_name="packets per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_packets_per_sec_unit = models.TextField(default="Mpps")
    output_throughput_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkMultiClusterCryptoPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="crypto_raw_speed")
    input_algorithm = models.CharField(max_length=30, default="")
    input_operation = models.CharField(max_length=30, default="")
    input_pkt_size = models.IntegerField(verbose_name="bytes", default=-1)
    input_key_size = models.IntegerField(verbose_name="Key Size", default=-1)
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Gbps", default=-1)
    output_latency_min = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_avg = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_max = models.IntegerField(verbose_name="ns", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    output_throughput_unit = models.TextField(default="Gbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class CryptoFastPathPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="crypto_fast_path")
    input_algorithm = models.CharField(max_length=30, default="")
    input_operation = models.CharField(max_length=30, default="")
    input_pkt_size = models.IntegerField(verbose_name="bytes", default=-1)
    input_key_size = models.IntegerField(verbose_name="Key Size", default=-1)
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_throughput = models.FloatField(verbose_name="Throughput", default=-1)
    output_latency_min = models.IntegerField(verbose_name="Latency min", default=-1)
    output_latency_avg = models.IntegerField(verbose_name="Latency avg", default=-1)
    output_latency_max = models.IntegerField(verbose_name="Latency max", default=-1)
    output_ops_per_sec_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_throughput_unit = models.TextField(default=PerfUnit.UNIT_GBITS_PER_SEC)
    output_latency_min_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_latency_avg_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_latency_max_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkLookupEnginePerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_test = models.CharField(max_length=30, default="le_test_perf", choices=[(0, "le_test_perf")])
    input_memory = models.CharField(max_length=100, default="", choices=[(0, "HT HBM non-coherent - FP HBM non-coherent"), (1, "HT HBM coherent     - FP HBM coherent"), (2, "HT DDR non-coherent - FP DDR non-coherent"), (3, "HT DDR coherent     - FP DDR coherent"), (4, "TCAM")])
    output_lookup_per_sec_min = models.IntegerField(verbose_name="lookups per sec", default=-1)
    output_lookup_per_sec_avg = models.IntegerField(verbose_name="lookups per sec", default=-1)
    output_lookup_per_sec_max = models.IntegerField(verbose_name="lookups per sec", default=-1)
    output_lookup_per_sec_min_unit = models.TextField(default="lookups/sec")
    output_lookup_per_sec_avg_unit = models.TextField(default="lookups/sec")
    output_lookup_per_sec_max_unit = models.TextField(default="lookups/sec")
    input_operation = models.TextField(default="")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkZipDeflatePerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_type = models.CharField(max_length=30, default="", choices=[(0, "Deflate")])
    input_operation = models.CharField(max_length=30, default="", choices=[(0, "Compress"), (1, "Decompress")])
    input_effort = models.CharField(max_length=30, default="", choices=[(0, "0"), (1, "3"), (2, "4"), (3, "5"), (4, "8"), (5, "9"), (6, "10"), (7, "11")])
    output_bandwidth_avg = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_total = models.IntegerField(verbose_name="Kbps", default=-1)
    output_latency_min = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_avg = models.BigIntegerField(verbose_name="ns", default=-1)
    output_latency_max = models.IntegerField(verbose_name="ns", default=-1)
    output_iops = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_bandwidth_avg_unit = models.TextField(default="Gbps")
    output_bandwidth_total_unit = models.TextField(default="Gbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_iops_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkZipLzmaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_type = models.CharField(max_length=30, default="", choices=[(0, "LZMA")])
    input_operation = models.CharField(max_length=30, default="", choices=[(0, "Compress"), (1, "Decompress")])
    input_effort = models.CharField(max_length=30, default="", choices=[(0, "8"), (1, "9"), (2, "10"), (3, "11")])
    output_bandwidth_avg = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_total = models.IntegerField(verbose_name="Kbps", default=-1)
    output_latency_min = models.IntegerField(verbose_name="ns", default=-1)
    output_latency_avg = models.BigIntegerField(verbose_name="ns", default=-1)
    output_latency_max = models.IntegerField(verbose_name="ns", default=-1)
    output_iops = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_bandwidth_avg_unit = models.TextField(default="Gbps")
    output_bandwidth_total_unit = models.TextField(default="Gbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_iops_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkRcnvmeReadWritePerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_operation = models.TextField( default="")
    input_io_type = models.TextField(default="")
    input_dev_access = models.TextField(default="")
    input_num_ctrlrs = models.IntegerField(default=-1)
    input_num_threads = models.IntegerField(default=-1)
    input_qdepth = models.IntegerField(default=-1)
    input_io_size = models.IntegerField(default=-1)
    input_ctrlr_id = models.IntegerField(default=-1)
    input_model = models.TextField(default="")
    input_fw_rev = models.TextField(default="")
    input_serial = models.TextField(default="")
    input_pci_vendor_id = models.TextField(default="")
    input_pci_device_id = models.TextField(default="")
    input_count = models.IntegerField(default=-1)
    input_metric_name = models.TextField(default="")
    output_bandwidth = models.FloatField(verbose_name="Mbps", default=-1)
    output_latency_min = models.BigIntegerField(verbose_name="Min nsecs", default=-1)
    output_latency_avg = models.BigIntegerField(verbose_name="Avg nsecs", default=-1)
    output_latency_max = models.BigIntegerField(verbose_name="Max nsecs", default=-1)
    output_iops = models.BigIntegerField(verbose_name="ops per sec", default=-1)
    output_bandwidth_unit = models.TextField(default="Mbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_iops_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkRcnvmeReadWriteAllPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_operation = models.TextField( default="")
    input_io_type = models.TextField(default="")
    input_dev_access = models.TextField(default="")
    input_num_ctrlrs = models.TextField(default="")
    input_num_threads = models.IntegerField(default=-1)
    input_qdepth = models.IntegerField(default=-1)
    input_io_size = models.IntegerField(default=-1)
    input_ctrlr_id = models.IntegerField(default=-1)
    input_model = models.TextField(default="")
    input_fw_rev = models.TextField(default="")
    input_serial = models.TextField(default="")
    input_pci_vendor_id = models.TextField(default="")
    input_pci_device_id = models.TextField(default="")
    input_count = models.IntegerField(default=-1)
    input_metric_name = models.TextField(default="")
    output_bandwidth = models.FloatField(verbose_name="Mbps", default=-1)
    output_latency_min = models.BigIntegerField(verbose_name="Min nsecs", default=-1)
    output_latency_avg = models.BigIntegerField(verbose_name="Avg nsecs", default=-1)
    output_latency_max = models.BigIntegerField(verbose_name="Max nsecs", default=-1)
    output_iops = models.BigIntegerField(verbose_name="ops per sec", default=-1)
    output_bandwidth_unit = models.TextField(default="Mbps")
    output_latency_min_unit = models.TextField(default="nsecs")
    output_latency_avg_unit = models.TextField(default="nsecs")
    output_latency_max_unit = models.TextField(default="nsecs")
    output_iops_unit = models.TextField(default="ops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkDfaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_latency = models.BigIntegerField(verbose_name="nsecs", default=-1)
    output_latency_unit = models.TextField(default="nsecs")
    output_bandwidth = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkNfaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_latency = models.BigIntegerField(verbose_name="nsecs", default=-1)
    output_latency_unit = models.TextField(default="nsecs")
    output_bandwidth = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_unit = models.TextField(default="Gbps")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkJpegPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_operation = models.TextField(verbose_name="Operation")
    output_average_bandwidth = models.FloatField(verbose_name="Average bandwidth", default=-1)
    output_total_bandwidth = models.IntegerField(verbose_name="Total bandwidth", default=-1)
    output_average_bandwidth_unit = models.TextField(default="Gbps")
    output_total_bandwidth_unit = models.TextField(default="Gbps")
    input_count = models.IntegerField(verbose_name="Count", default=0)
    input_image = models.TextField(verbose_name="Image", default="None")
    output_iops = models.IntegerField(verbose_name="IOPS", default=-1)
    output_max_latency = models.IntegerField(verbose_name="Max latency", default=-1)
    output_min_latency = models.IntegerField(verbose_name="Min latency", default=-1)
    output_average_latency = models.IntegerField(verbose_name="Average latency", default=-1)
    output_compression_ratio = models.FloatField(verbose_name="Compression ratio", default=-1)
    output_percentage_savings = models.FloatField(verbose_name="Percentage savings", default=-1)
    output_iops_unit = models.TextField(default="ops")
    output_max_latency_unit = models.TextField(default="nsecs")
    output_min_latency_unit = models.TextField(default="nsecs")
    output_average_latency_unit = models.TextField(default="nsecs")
    output_compression_ratio_unit = models.TextField(default="number")
    output_percentage_savings_unit = models.TextField(default="number")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class FlowTestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="hw_hsu_test", choices=[(0, "hw_hsu_test")])
    input_iterations = models.IntegerField(default=-1)
    output_time = models.IntegerField(verbose_name="seconds", default=-1)
    output_time_unit = models.TextField(default="secs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class F1FlowTestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="hw_hsu_test", choices=[(0, "hw_hsu_test")])
    input_iterations = models.IntegerField(default=-1)
    output_time = models.IntegerField(verbose_name="seconds", default=-1)
    output_time_unit = models.TextField(default="secs")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class BootTimePerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_firmware_boot_time = models.FloatField(verbose_name="Firmware" ,default=-1)
    output_flash_type_boot_time = models.FloatField(verbose_name="Flash type detection" ,default=-1)
    output_eeprom_boot_time = models.FloatField(verbose_name="EEPROM Loading", default=-1)
    output_sbus_boot_time = models.FloatField(verbose_name="SBUS Loading", default=-1)
    output_host_boot_time = models.FloatField(verbose_name="Host BOOT", default=-1)
    output_main_loop_boot_time = models.FloatField(verbose_name="Main Loop", default=-1)
    output_boot_success_boot_time = models.FloatField(verbose_name="Boot success", default=-1)
    output_init_mmc_time = models.FloatField(verbose_name="MMC INIT" ,default=-1)
    output_boot_read_mmc_time = models.FloatField(verbose_name="Boot Load" ,default=-1)
    output_funos_read_mmc_time = models.FloatField(verbose_name="FunOS Load", default=-1)
    output_funos_load_elf_time = models.FloatField(verbose_name="FunOS ELF Load", default=-1)
    output_firmware_boot_time_unit = models.TextField(default="msecs")
    output_flash_type_boot_time_unit = models.TextField(default="msecs")
    output_eeprom_boot_time_unit = models.TextField(default="msecs")
    output_sbus_boot_time_unit = models.TextField(default="msecs")
    output_host_boot_time_unit = models.TextField(default="msecs")
    output_main_loop_boot_time_unit = models.TextField(default="msecs")
    output_boot_success_boot_time_unit = models.TextField(default="msecs")
    output_init_mmc_time_unit = models.TextField(default="msecs")
    output_boot_read_mmc_time_unit = models.TextField(default="msecs")
    output_funos_read_mmc_time_unit = models.TextField(default="msecs")
    output_funos_load_elf_time_unit = models.TextField(default="msecs")
    output_all_vps_online = models.FloatField(verbose_name="All VPs Online", default=-1)
    output_parsing_config = models.FloatField(verbose_name="Parsing Config time", default=-1)
    output_parsing_config_end = models.FloatField(verbose_name="Parsing Config end", default=-1)
    output_sending_host_booted_message = models.FloatField(verbose_name="Host Booted Message", default=-1)
    output_all_vps_online_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_parsing_config_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_parsing_config_end_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_sending_host_booted_message_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class HuRawVolumePerformance(models.Model):
    output_latency = models.IntegerField(verbose_name="Latency", default=-1)
    output_bandwidth = models.IntegerField(verbose_name="Bandwidth", default=-1)
    output_iops = models.IntegerField(verbose_name="IO per second", default=-1)
    #input_threads = models.IntegerField(verbose_name="Number of threads", default=-1, choices=[[0, 1.0]])
    input_testbed = models.CharField(max_length=30, verbose_name="Testbed", default="storage1", choices=[(0, "storage1"),(1.0,"storage2"),(2.0, "storagenw")])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class FunMagentPerformanceTest(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="fun_magent_perf_test", choices=[(0, "fun_magent_perf_test")])
    input_metric_name = models.CharField(max_length=40, default="fun_magent_rate_malloc_free_per_sec",
                                         choices=[(0, "fun_magent_rate_malloc_free_per_sec")])
    output_latency = models.IntegerField(verbose_name="KOps/sec", default=-1)
    output_latency_unit = models.TextField(default="Kops")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)


    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class WuStackSpeedTestPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="wustack_speed_test", choices=[(0, "wustack_speed_test")])
    input_metric_name = models.CharField(max_length=40, default="wustack_alloc_free_cycles",
                                         choices=[(0, "wustack_alloc_free_cycles")])
    output_average = models.IntegerField(verbose_name="Alloc/free cycles average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class VoltestLsvPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_read_write_iops = models.BigIntegerField(verbose_name="ReadWrite ops per sec", default=-1)
    output_read_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_write_bandwidth = models.FloatField(verbose_name="ReadWrite Throughput in Mbps", default=-1)
    output_read_write_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class VoltestLsv4Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_read_write_iops = models.BigIntegerField(verbose_name="ReadWrite ops per sec", default=-1)
    output_read_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_write_bandwidth = models.FloatField(verbose_name="ReadWrite Throughput in Mbps", default=-1)
    output_read_write_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class MileStoneMarkers(models.Model):
    metric_id = models.IntegerField(default=-1)
    milestone_date = models.DateTimeField(verbose_name="Date", default=datetime.now)
    milestone_name = models.TextField(default="")

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PerformanceMetricsDag(FunModel):
    date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    metrics_dag = JSONField(default=[])

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class ShaxPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()
    class Meta:
        model = ShaxPerformance
        fields = "__all__"

class BcopyPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()
    class Meta:
        model = BcopyPerformance
        fields = "__all__"


class VoltestPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()

    class Meta:
        model = VoltestPerformance
        fields = "__all__"


class BcopyFloodDmaPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()

    class Meta:
        model = BcopyFloodDmaPerformance
        fields = "__all__"


class LsvZipCryptoPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()

    class Meta:
        model = LsvZipCryptoPerformance
        fields = "__all__"


class EcVolPerformanceSerialzer(ModelSerializer):
    input_date_time = serializers.DateTimeField()

    class Meta:
        model = EcVolPerformance
        fields = "__all__"


class NuTransitPerformanceSerializer(ModelSerializer):
    input_date_time = serializers.DateTimeField()

    class Meta:
        model = NuTransitPerformance
        fields = "__all__"

class AlibabaRdmaPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    input_test = models.TextField(verbose_name="Test type", default="")
    input_operation = models.TextField(verbose_name="operation type", default="")
    input_size_latency = models.IntegerField(verbose_name="latency size in bytes", default=-1)
    input_size_bandwidth = models.IntegerField(verbose_name="bandwidth size in bytes", default=-1)
    input_qp = models.IntegerField(verbose_name="QP", default=-1)
    input_fcp = models.BooleanField(default=False)
    input_mtu = models.IntegerField(verbose_name="MTU", default=-1)
    input_hosts = models.IntegerField(verbose_name="HOSTS", default=-1)
    
    output_read_avg_latency = models.FloatField(verbose_name="read average latency (usec)", default=-1)
    output_write_avg_latency = models.FloatField(verbose_name="write average latency (usec)", default=-1)
    output_read_min_latency = models.FloatField(verbose_name="read min latency(usec)", default=-1)
    output_write_min_latency = models.FloatField(verbose_name="write min latency (usec)", default=-1)
    output_read_max_latency = models.FloatField(verbose_name="read max latency(usec)", default=-1)
    output_write_max_latency = models.FloatField(verbose_name="write max latency(usec)", default=-1)
    output_read_99_latency = models.FloatField(verbose_name="read 99% latency", default=-1)
    output_write_99_latency = models.FloatField(verbose_name="write 99% latency", default=-1)
    output_read_99_99_latency = models.FloatField(verbose_name="read 99.99% latency", default=-1)
    output_write_99_99_latency = models.FloatField(verbose_name="write 99.99% latency", default=-1)
    output_read_bandwidth = models.FloatField(verbose_name="read output bandwidth", default=-1)
    output_write_bandwidth = models.FloatField(verbose_name="write output bandwidth", default=-1)
    output_read_msg_rate = models.FloatField(verbose_name="read Message rate (Mpps)", default=-1)
    output_write_msg_rate = models.FloatField(verbose_name="write Message rate (Mpps)", default=-1)

    output_read_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_min_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_min_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_max_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_max_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_GBITS_PER_SEC)
    output_write_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_GBITS_PER_SEC)
    output_read_msg_rate_unit = models.TextField(default=PerfUnit.UNIT_MPPS)
    output_write_msg_rate_unit = models.TextField(default=PerfUnit.UNIT_MPPS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return (str(self.__dict__))


class SoakFlowsBusyLoop10usecs(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_name = models.CharField(max_length=30, verbose_name="soak flows busy loop 10usecs app name", default="busy_loop_10usecs")
    input_metric_name = models.CharField(max_length=30, verbose_name='Metric name', default="busy_loop_10usecs")
    input_platform = models.TextField(default=FunPlatform.F1)
    input_variation = models.FloatField(verbose_name='variation', default=-1)
    input_max_variation = models.FloatField(verbose_name='maximum variation', default=-1)
    input_min_duration = models.FloatField(verbose_name='minimum duration', default=-1)
    input_max_duration = models.FloatField(verbose_name='maximum duration', default=-1)
    input_duration = models.FloatField(verbose_name='duration', default=-1)
    input_num_flows = models.FloatField(verbose_name='Number of flows', default=-1)
    input_num_ops = models.FloatField(verbose_name='Number of operations', default=-1)
    input_warm_up = models.FloatField(verbose_name="warm up", default=-1)

    output_busy_loops_value = models.FloatField(verbose_name="maximum number of busy-loops", default=-1)
    output_busy_loops_value_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return (str(self.__dict__))


class SoakFlowsMemcpy1MBNonCoh(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_name = models.CharField(max_length=60, verbose_name="soak flows dma memcpy test 64KB", default="soak_flows_dma_memcpy_test_64KB")
    input_metric_name = models.CharField(max_length=60, verbose_name='Metric name', default="soak_flows_dma_memcpy_test_64kB")
    input_platform = models.TextField(default=FunPlatform.F1)
    input_variation = models.FloatField(verbose_name='variation', default=-1)
    input_max_variation = models.FloatField(verbose_name='maximum variation', default=-1)
    input_min_duration = models.FloatField(verbose_name='minimum duration', default=-1)
    input_max_duration = models.FloatField(verbose_name='maximum duration', default=-1)
    input_duration = models.FloatField(verbose_name='duration', default=-1)
    input_num_flows = models.FloatField(verbose_name='Number of flows', default=-1)
    input_num_ops = models.FloatField(verbose_name='Number of operations', default=-1)
    input_warm_up = models.FloatField(verbose_name="warm up", default=-1)

    output_dma_memcpy_value = models.FloatField(verbose_name="maximum number of busy-loops", default=-1)
    output_dma_memcpy_value_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return (str(self.__dict__))


class VoltestBlt1Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    input_blt_instance = models.IntegerField(verbose_name="BLT instance", default=-1)

    output_min_latency = models.FloatField(verbose_name="Minimun latency", default=-1)
    output_max_latency = models.FloatField(verbose_name="Maximum latency", default=-1)
    output_avg_latency = models.FloatField(verbose_name="Average latency", default=-1)
    output_iops = models.FloatField(verbose_name="IOPS", default=-1)
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)

    output_min_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_max_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    run_time_id = models.IntegerField(default=None, null=True)


class VoltestBlt8Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    input_blt_instance = models.IntegerField(verbose_name="BLT instance", default=-1)

    output_min_latency = models.FloatField(verbose_name="Minimun latency", default=-1)
    output_max_latency = models.FloatField(verbose_name="Maximum latency", default=-1)
    output_avg_latency = models.FloatField(verbose_name="Average latency", default=-1)
    output_iops = models.FloatField(verbose_name="IOPS", default=-1)
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)

    output_min_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_max_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    run_time_id = models.IntegerField(default=None, null=True)


class VoltestBlt12Performance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")
    input_blt_instance = models.IntegerField(verbose_name="BLT instance", default=-1)

    output_min_latency = models.FloatField(verbose_name="Minimun latency", default=-1)
    output_max_latency = models.FloatField(verbose_name="Maximum latency", default=-1)
    output_avg_latency = models.FloatField(verbose_name="Average latency", default=-1)
    output_iops = models.FloatField(verbose_name="IOPS", default=-1)
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)

    output_min_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_max_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_NSECS)
    output_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    run_time_id = models.IntegerField(default=None, null=True)


class InspurSingleDiskFailurePerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_num_hosts = models.IntegerField(verbose_name="Number of hosts", default=-1)
    input_num_f1s = models.IntegerField(verbose_name="Number of F1's", default=1)
    input_volume_size = models.IntegerField(verbose_name="Volume size", default=-1)
    input_test_file_size = models.IntegerField(verbose_name="Test file size", default=-1)
    input_job_name = models.CharField(verbose_name="Job name", max_length=50, default="")

    output_base_file_copy_time = models.FloatField(verbose_name="Base file copy time (sec)", default=-1)
    output_copy_time_during_plex_fail = models.FloatField(verbose_name="File copy time during plex fail(sec)", default=-1)
    output_file_copy_time_during_rebuild = models.FloatField(verbose_name="File copy time during rebuild (sec)", default=-1)
    output_plex_rebuild_time = models.FloatField(verbose_name="Plex rebuild time (sec)", default=-1)

    output_base_file_copy_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_copy_time_during_plex_fail_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_file_copy_time_during_rebuild_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_plex_rebuild_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return (str(self.__dict__))


class InspurDataReconstructionPerformance(models.Model):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_num_hosts = models.IntegerField(verbose_name="Number of hosts", default=-1)
    input_block_size = models.TextField(verbose_name="Block size", default="")
    input_io_depth = models.IntegerField(verbose_name="IO depth", default=-1)
    input_size =models.TextField(verbose_name="Input size", default="")
    input_operation = models.TextField(verbose_name="Operation type", default="")
    input_fio_job_name = models.TextField(verbose_name="Input FIO job name", default="")

    output_write_iops = models.IntegerField(verbose_name="Write IOPS", default=-1)
    output_read_iops = models.IntegerField(verbose_name="Read IOPS", default=-1)
    output_write_throughput = models.FloatField(verbose_name="Write throughput", default=-1)
    output_read_throughput = models.FloatField(verbose_name="Read throughput", default=-1)
    output_write_avg_latency = models.IntegerField(verbose_name="Write avg latency", default=-1)
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency", default=-1)
    output_write_99_99_latency = models.IntegerField(verbose_name="Write 99.99% latency", default=-1)
    output_read_avg_latency = models.IntegerField(verbose_name="Read avg latency", default=-1)
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency", default=-1)
    output_read_99_99_latency = models.IntegerField(verbose_name="Read 99.99% latency", default=-1)
    output_plex_rebuild_time = models.IntegerField(verbose_name="Plex rebuild time", default=-1)

    output_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_write_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_read_throughput_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    output_write_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_avg_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_90_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_95_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_99_latency_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_plex_rebuild_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        return (str(self.__dict__))


class PowerPerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    output_fs_power = models.FloatField(verbose_name="FS power", default=-1)
    output_f1_0_power = models.FloatField(verbose_name="F1_0 power", default=-1)
    output_f1_1_power = models.FloatField(verbose_name="F1_1 power", default=-1)

    output_fs_power_unit = models.TextField(default=PerfUnit.UNIT_WATT)
    output_f1_0_power_unit = models.TextField(default=PerfUnit.UNIT_WATT)
    output_f1_1_power_unit = models.TextField(default=PerfUnit.UNIT_WATT)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class RdsClientPerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_num_hosts = models.IntegerField(verbose_name="Number of hosts", default=-1)
    input_msg_rate = models.IntegerField(verbose_name="Message rate", default=-1)
    input_num_connection = models.IntegerField(verbose_name="Number of connections", default=-1)
    output_aggregate_bandwidth = models.FloatField(verbose_name="Aggregate Bandwidth", default=-1)

    output_aggregate_bandwidth_unit = models.TextField(default=PerfUnit.UNIT_MBITS_PER_SEC)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class NvmeFcpPerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_platform = models.TextField(default=FunPlatform.F1)
    input_version = models.CharField(verbose_name="Version", max_length=50, default="")

    input_block_size = models.IntegerField(verbose_name="Block size", default=-1)
    input_test_case = models.TextField(verbose_name="Test case", default="")
    input_operation = models.TextField(verbose_name="Operation", default="")
    input_volumes = models.IntegerField(verbose_name="Volumes", default=-1)
    output_read_iops = models.FloatField(verbose_name="Read IOPS", default=-1)
    output_read_bw = models.FloatField(verbose_name="Read bandwidth", default=-1)
    output_read_latency_avg = models.FloatField(verbose_name="Read latency avg", default=-1)
    output_read_latency_50 = models.FloatField(verbose_name="Read latency 50", default=-1)
    output_read_latency_90 = models.FloatField(verbose_name="Read latency 90", default=-1)
    output_read_latency_95 = models.FloatField(verbose_name="Read latency 95", default=-1)
    output_read_latency_99 = models.FloatField(verbose_name="Read latency 99", default=-1)
    output_read_latency_9950 = models.FloatField(verbose_name="Read latency 99.50", default=-1)
    output_read_latency_9999 = models.FloatField(verbose_name="Read latency 99.99", default=-1)

    output_write_bw = models.FloatField(verbose_name="Write bandwidth", default=-1)
    output_write_latency_avg = models.FloatField(verbose_name="Write latency avg", default=-1)
    output_write_latency_50 = models.FloatField(verbose_name="Write latency 50", default=-1)
    output_write_latency_90 = models.FloatField(verbose_name="Write latency 90", default=-1)
    output_write_latency_95 = models.FloatField(verbose_name="Write latency 95", default=-1)
    output_write_latency_99 = models.FloatField(verbose_name="Write latency 99", default=-1)
    output_write_latency_9950 = models.FloatField(verbose_name="Write latency 99.50", default=-1)
    output_write_latency_9999 = models.FloatField(verbose_name="Write latency 99.99", default=-1)

    output_read_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_read_bw_unit = models.TextField(default=PerfUnit.UNIT_GBITS_PER_SEC)
    output_read_latency_avg_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_50_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_90_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_95_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_99_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_9950_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_read_latency_9999_unit = models.TextField(default=PerfUnit.UNIT_USECS)

    output_write_iops_unit = models.TextField(default=PerfUnit.UNIT_OPS)
    output_write_bw_unit = models.TextField(default=PerfUnit.UNIT_GBITS_PER_SEC)
    output_write_latency_avg_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_50_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_90_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_95_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_99_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_9950_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    output_write_latency_9999_unit = models.TextField(default=PerfUnit.UNIT_USECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class FunOnDemandTotalTimePerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)

    output_total_time = models.FloatField(verbose_name="Total Time", default=-1)
    output_total_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PrBuildTotalTimePerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)

    output_total_time = models.FloatField(verbose_name="Total Time", default=-1)
    output_total_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class IntegrationJobBuildTimePerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)

    output_total_time = models.FloatField(verbose_name="Total Time", default=-1)
    output_total_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class FlakyTestsFailurePerformance(FunModel):
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)

    output_failure_percentage = models.FloatField(verbose_name="Failure Percentage", default=-1)
    output_failure_percentage_unit = models.TextField(default=PerfUnit.UNIT_NUMBER)
    run_time_id = models.IntegerField(default=None, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class RawVolumeNvmeTcpMultiHostPerformance(FunModel):
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_num_hosts = models.IntegerField(verbose_name="Number of hosts")
    input_num_ssd = models.IntegerField(verbose_name="Number of SSD(s)")
    input_num_dpu = models.IntegerField(verbose_name="Number of DPU(s) used")
    input_num_volume = models.IntegerField(verbose_name="Number of volume(s)")
    input_block_size = models.TextField(verbose_name="Block size")
    input_io_depth = models.IntegerField(verbose_name="IO depth")
    input_operation = models.TextField(verbose_name="Operation type")
    input_shared_volume = models.BooleanField(verbose_name="Shared volume", default=False)
    input_compression = models.BooleanField(verbose_name="Compression enabled")
    input_encryption = models.BooleanField(verbose_name="Encryption enabled")
    input_compression_effort = models.IntegerField(verbose_name="Compression effort")
    input_key_size = models.IntegerField(verbose_name="Key size")
    input_xtweak = models.IntegerField(verbose_name="Xtweak")
    input_io_size = models.TextField(verbose_name="IO size")
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])

    output_write_iops = models.IntegerField(verbose_name="Write IOPS", default=-1)
    output_read_iops = models.IntegerField(verbose_name="Read IOPS", default=-1)
    output_write_throughput = models.FloatField(verbose_name="Write throughput", default=-1)
    output_read_throughput = models.FloatField(verbose_name="Read throughput", default=-1)
    output_write_avg_latency = models.IntegerField(verbose_name="Write avg latency", default=-1)
    output_write_90_latency = models.IntegerField(verbose_name="Write 90% latency", default=-1)
    output_write_95_latency = models.IntegerField(verbose_name="Write 95% latency", default=-1)
    output_write_99_latency = models.IntegerField(verbose_name="Write 99% latency", default=-1)
    output_write_99_99_latency = models.IntegerField(verbose_name="Write 99.99% latency", default=-1)
    output_read_avg_latency = models.IntegerField(verbose_name="Read avg latency", default=-1)
    output_read_90_latency = models.IntegerField(verbose_name="Read 90% latency", default=-1)
    output_read_95_latency = models.IntegerField(verbose_name="Read 95% latency", default=-1)
    output_read_99_latency = models.IntegerField(verbose_name="Read 99% latency", default=-1)
    output_read_99_99_latency = models.IntegerField(verbose_name="Read 99.99% latency", default=-1)

    output_write_iops_unit = models.TextField(default="ops")
    output_read_iops_unit = models.TextField(default="ops")
    output_write_throughput_unit = models.TextField(default="Mbps")
    output_read_throughput_unit = models.TextField(default="Mbps")
    output_write_avg_latency_unit = models.TextField(default="usecs")
    output_write_90_latency_unit = models.TextField(default="usecs")
    output_write_95_latency_unit = models.TextField(default="usecs")
    output_write_99_latency_unit = models.TextField(default="usecs")
    output_write_99_99_latency_unit = models.TextField(default="usecs")
    output_read_avg_latency_unit = models.TextField(default="usecs")
    output_read_90_latency_unit = models.TextField(default="usecs")
    output_read_95_latency_unit = models.TextField(default="usecs")
    output_read_99_latency_unit = models.TextField(default="usecs")
    output_read_99_99_latency_unit = models.TextField(default="usecs")

    def __str__(self):
        return (str(self.__dict__))


class DataPlaneOperationsPerformance(FunModel):
    input_date_time = models.DateTimeField(verbose_name="Date time", default=datetime.now)
    input_volume_size = models.IntegerField(verbose_name="Volume size")
    input_total_volumes = models.IntegerField(verbose_name="Number of volumes")
    input_volume_type = models.TextField(verbose_name="Volume type")
    input_action_type = models.TextField(verbose_name="Action type")
    input_volume_size_unit = models.TextField(default=PerfUnit.UNIT_MB)
    input_concurrent = models.BooleanField(default=False)
    input_split_performance_data = models.TextField(verbose_name="Split perf data", default={})
    input_platform = models.TextField(default=FunPlatform.F1)
    run_time_id = models.IntegerField(default=None, null=True)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])


    output_total_time = models.FloatField(verbose_name="Total time taken", default=-1)
    output_avg_time = models.FloatField(verbose_name="Avg time taken", default=-1)

    output_total_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)
    output_avg_time_unit = models.TextField(default=PerfUnit.UNIT_SECS)

    def __str__(self):
        return (str(self.__dict__))