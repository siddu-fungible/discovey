from fun_settings import MAIN_WEB_APP
from django.db import models
from django.apps import apps
#from web.fun_test import apps
from fun_global import RESULTS, get_current_time, get_localized_time
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
import json
# from web.fun_test.site_state import site_state
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
import logging
import datetime
from datetime import datetime, timedelta
from django.contrib.postgres.fields import JSONField
from web.web_global import *
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

LAST_ANALYTICS_DB_STATUS_UPDATE = "last_status_update"
BASE_LINE_DATE = datetime(year=2018, month=4, day=1)

class MetricsGlobalSettings(models.Model):
    tolerance_percentage = models.FloatField(default=3.0)
    cache_valid = models.BooleanField(default=True)

class MetricsGlobalSettingsSerializer(ModelSerializer):

    class Meta:
        model = MetricsGlobalSettings
        fields = "__all__"


class TriageType:
    SCORES = "SCORES"
    PASS_FAIL = "PASS/FAIL"

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
    metric_id = models.IntegerField(default=-1)
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

class Triage(models.Model):
    metric_id = models.IntegerField(default=-1)
    metric_type = models.CharField(max_length=15, default=TriageType.SCORES)
    triage_id = models.IntegerField(default=-1)
    date_time = models.DateTimeField(default=datetime.now)
    degraded_suite_execution_id = models.IntegerField(default=-1)
    degraded_jenkins_job_id = models.IntegerField(default=-1)
    degraded_lsf_job_id = models.IntegerField(default=-1)
    degraded_git_commit = models.TextField(default="")
    degraded_build_properties = models.TextField(default="")
    stable_suite_execution_id = models.IntegerField(default=-1)
    stable_jenkins_job_id = models.IntegerField(default=-1)
    stable_lsf_job_id = models.IntegerField(default=-1)
    stable_git_commit = models.TextField(default="")
    stable_build_properties = models.TextField(default="")
    last_good_score = models.FloatField(default=-1)
    status = models.CharField(max_length=30, default=SchedulingStates.ACTIVE)
    max_tries = models.IntegerField(default=-1)
    faulty_commit = models.TextField(default="")
    boot_args = models.TextField(default="")
    fun_os_make_flags = models.TextField(default="")
    email = models.TextField(default="")

    def __str__(self):
        s = "{}:{} {} Score: {}".format(self.metric_id, self.triage_id, self.status, self.last_good_score)
        return s

class TriageFlow(models.Model):
    metric_id = models.IntegerField(default=-1)
    metric_type = models.CharField(max_length=15, default=TriageType.SCORES)
    triage_id = models.IntegerField(default=-1)
    triage_flow_id = models.IntegerField(default=-1, unique=True)
    date_time = models.DateTimeField(default=datetime.now)
    score = models.FloatField(default=-1)
    suite_execution_id = models.IntegerField(default=-1)
    jenkins_job_id = models.IntegerField(default=-1)
    lsf_job_id = models.IntegerField(default=-1)
    status = models.CharField(max_length=30, default=SchedulingStates.WAITING)
    git_commit = models.TextField(default="")
    committer = models.TextField(default="")
    build_properties = models.TextField(default="")
    boot_args = models.TextField(default="")
    fun_os_make_flags = models.TextField(default="")
    email = models.TextField(default="")

    def __str__(self):
        s = "{}:{} {} Score: {}".format(self.metric_id, self.triage_id, self.status, self.score)
        return s

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

    def __str__(self):
        return "{}: {} : {} : {}".format(self.internal_chart_name, self.chart_name, self.metric_model_name, self.metric_id)

    def get_children(self):
        return json.loads(self.children)

    def get_children_weights(self):
        return json.loads(self.children_weights)

    def add_child(self, child_id):
        children = json.loads(self.children)
        if child_id not in children:
            children.append(child_id)
            self.children = json.dumps(children)
            self.save()

    def add_child_weight(self, child_id, weight):
        children_weights = json.loads(self.children_weights)
        children_weights = {int(x): y for x, y in children_weights.iteritems()}
        children_weights[int(child_id)] = weight
        self.children_weights = json.dumps(children_weights)
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
                    if model.objects.first().interpolation_allowed:
                        self.remove_duplicates(model=model, from_date=earlier_day, to_date=today)
                        entries = model.objects.filter(**d).order_by(order_by)
                        i = entries.count()
                if entries.count() < (number_of_records - 1):
                    # let's fix it up
                    if model.objects.first().interpolation_allowed:
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

class LastTriageFlowId(models.Model):
    last_id = models.IntegerField(unique=True, default=100)

    @staticmethod
    def get_next_id():
        if not LastTriageFlowId.objects.count():
            LastTriageFlowId().save()
        last = LastTriageFlowId.objects.all().last()
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
    tag = "analytics"


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
    tag = "analytics"
    interpolation_allowed = models.BooleanField(default=True)
    interpolated = models.BooleanField(default=False)



class PerformanceBlt(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1_block_size = models.CharField(max_length=20, choices=[(0, "4K"), (1, "8K"), (2, "16K")], verbose_name="Block size")
    input2_mode = models.CharField(max_length=20, choices=[(0, "Read"), (1, "Read-Write")], verbose_name="R/W Mode")
    output1_iops = models.IntegerField(verbose_name="IOPS")
    output2_bw = models.IntegerField(verbose_name="Band-width")
    output3_latency = models.IntegerField(verbose_name="Latency")
    tag = "analytics"


class PerformanceIkv(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1_put_value_size = models.IntegerField(verbose_name="PUT Value size", choices=[(0, 4096), (1, 8192)])
    output1_put_per_seccond = models.IntegerField(verbose_name="PUTs per second")
    tag = "analytics"


class VolumePerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

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
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

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
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

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

class AllocSpeedPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        return "{}..{}..{}..{}..{}..{}..{}".format(self.key, self.output_one_malloc_free_wu, self.output_one_malloc_free_threaded,
                                       self.output_one_malloc_free_classic_min, self.output_one_malloc_free_classic_avg,
                                       self.output_one_malloc_free_classic_max, self.input_date_time)


class WuLatencyAllocStack(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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

    def __str__(self):
        return "{}..{}..{}..{}".format(self.key, self.output_min, self.output_avg, self.output_max)

class WuLatencyUngated(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_ndata_min = models.IntegerField(verbose_name="ndata min", default=8)
    input_ndata_max = models.IntegerField(verbose_name="ndata min", default=8)
    input_nparity_min = models.IntegerField(verbose_name="nparity min", default=4)
    input_stridelen_min = models.IntegerField(verbose_name="strideline min", default=4096)
    input_stridelen_max = models.IntegerField(verbose_name="strideline max", default=4096)

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

    '''
     min_ndata=8 
     max_ndata=8 
     min_nparity=4 
     max_nparity=4 
     min_stridelen=4096 max_stridelen=4096 numthreads=1
    '''

class BcopyPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_iterations = models.IntegerField(verbose_name="Iterations", default=10)
    input_coherent = models.TextField(verbose_name="Coherent/Non", default="Coherent", choices=[(0, "Coherent"), (1, "Non-coherent")])
    input_plain = models.TextField(verbose_name="Plain/DMA", default="Plain", choices=[(0, "Plain"), (1, "DMA")])
    input_size = models.IntegerField(verbose_name="Size in KB", choices=[(0, "4"), (1, "8"), (2, "16"), (3, "32"), (4, "64")])
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

    def __str__(self):
        return str(self.__dict__)


class BcopyFloodDmaPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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

    def __str__(self):
        return str(self.__dict__)


class EcVolPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class NuTransitPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    interpolated = models.BooleanField(default=False)
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
    input_number_flows = models.IntegerField(verbose_name="Number of flows", default=512000)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="UDP")

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkJuniperNetworkingPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    interpolated = models.BooleanField(default=False)
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.FloatField(verbose_name="Frame Size")
    output_throughput = models.FloatField(verbose_name="Throughput in Gbps")
    output_latency_avg = models.FloatField(verbose_name="Latency Avg in us")
    output_latency_max = models.FloatField(verbose_name="Latency Max in us")
    output_latency_min = models.FloatField(verbose_name="Latency Min in us")
    output_jitter_min = models.FloatField(verbose_name="Jitter min in us")
    output_jitter_max = models.FloatField(verbose_name="Jitter max in us")
    output_jitter_avg = models.FloatField(verbose_name="Jitter avg in us")
    output_pps = models.FloatField(verbose_name="Packets per sec")
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
    input_number_flows = models.IntegerField(verbose_name="Number of flows", default=0)
    input_offloads = models.BooleanField(default=False)
    input_protocol = models.TextField(default="UDP")

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class VoltestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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

    def __str__(self):
        return "{}: {}".format(self.input_date_time, self.output_VOL_TYPE_BLK_LSV_write_Bandwidth_total)

class WuDispatchTestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="dispatch_speed_test", choices=[(0, "dispatch_speed_test")])
    input_metric_name = models.CharField(max_length=30, default="wu_dispatch_latency_cycles", choices=[(0, "wu_dispatch_latency_cycles")])
    output_average = models.IntegerField(verbose_name="Output WU Dispatch Performanmce Test Average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class WuSendSpeedTestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="wu_send_speed_test", choices=[(0, "wu_send_speed_test")])
    input_metric_name = models.CharField(max_length=40, default="wu_send_ungated_latency_cycles", choices=[(0, "wu_send_ungated_latency_cycles")])
    output_average = models.IntegerField(verbose_name="Output WU Send Speed Performanmce Test Average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakFunMallocPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="soak_malloc_fun_malloc", choices=[(0, "soak_malloc_fun_malloc")])
    input_metric_name = models.CharField(max_length=40, default="soak_two_fun_malloc_fun_free", choices=[(0, "soak_two_fun_malloc_fun_free")])
    output_ops_per_sec = models.IntegerField(verbose_name="Soak Fun Malloc Test ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakClassicMallocPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="soak_malloc_classic", choices=[(0, "soak_malloc_classic")])
    input_metric_name = models.CharField(max_length=40, default="soak_two_classic_malloc_free", choices=[(0, "soak_two_classic_malloc_free")])
    output_ops_per_sec = models.IntegerField(verbose_name="Soak Classic Malloc Test ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeRsaPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_rsa_crt_dec_no_pad_soak", choices=[(0, "pke_rsa_crt_dec_no_pad_soak")])
    input_metric_name = models.CharField(max_length=40, default="RSA_CRT_2048_decryptions", choices=[(0, "RSA_CRT_2048_decryptions")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeRsa4kPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=50, default="pke_rsa_crt_dec_no_pad_4096_soak", choices=[(0, "pke_rsa_crt_dec_no_pad_4096_soak")])
    input_metric_name = models.CharField(max_length=40, default="RSA_CRT_4096_decryptions", choices=[(0, "RSA_CRT_4096_decryptions")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeEcdh256Performance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_ecdh_soak_256", choices=[(0, "pke_ecdh_soak_256")])
    input_metric_name = models.CharField(max_length=40, default="ECDH_P256", choices=[(0, "ECDH_P256")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkPkeEcdh25519Performance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_ecdh_soak_25519", choices=[(0, "pke_ecdh_soak_25519")])
    input_metric_name = models.CharField(max_length=40, default="ECDH_25519", choices=[(0, "ECDH_25519")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops per sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PkeX25519TlsSoakPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_x25519_2k_tls_soak", choices=[(0, "pke_x25519_2k_tls_soak")])
    input_metric_name = models.CharField(max_length=40, default="ECDHE_RSA X25519 RSA 2K", choices=[(0, "ECDHE_RSA X25519 RSA 2K")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops/sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class PkeP256TlsSoakPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="pke_p256_2k_tls_soak", choices=[(0, "pke_p256_2k_tls_soak")])
    input_metric_name = models.CharField(max_length=40, default="ECDHE_RSA P256 RSA 2K", choices=[(0, "ECDHE_RSA P256 RSA 2K")])
    output_ops_per_sec = models.IntegerField(verbose_name="ops/sec", default=-1)
    output_ops_per_sec_unit = models.TextField(default="ops")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakDmaMemcpyCoherentPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakDmaMemcpyNonCoherentPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class SoakDmaMemsetPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_size = models.TextField(verbose_name="Size")
    input_operation = models.TextField(verbose_name="Operation")
    input_log_size = models.TextField(verbose_name="Log Size")
    input_coherent = models.BooleanField(default=True)
    output_bandwidth_unit = models.TextField(default="GBps")
    input_metric_name = models.TextField(verbose_name="Metric Name", default="")
    output_bandwidth = models.FloatField(verbose_name="Bandwidth", default=-1)
    input_unit = models.TextField(default="GBps")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkCryptoPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkMultiClusterCryptoPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkLookupEnginePerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkZipDeflatePerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkZipLzmaPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkRcnvmeReadWritePerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_operation = models.TextField( default="")
    input_io_type = models.TextField(default="")
    input_dev_access = models.TextField(default="")
    input_num_ctrlrs = models.IntegerField(default=-1)
    input_num_threads = models.IntegerField(default=-1)
    input_qdepth = models.IntegerField(default=-1)
    input_total_numios = models.IntegerField(default=-1)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkDfaPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_latency = models.BigIntegerField(verbose_name="nsecs", default=-1)
    output_latency_unit = models.TextField(default="nsecs")
    output_bandwidth = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_unit = models.TextField(default="Gbps")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkNfaPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    output_latency = models.BigIntegerField(verbose_name="nsecs", default=-1)
    output_latency_unit = models.TextField(default="nsecs")
    output_bandwidth = models.FloatField(verbose_name="Gbps", default=-1)
    output_bandwidth_unit = models.TextField(default="Gbps")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class TeraMarkJpegPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class FlowTestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="hw_hsu_test", choices=[(0, "hw_hsu_test")])
    input_iterations = models.IntegerField(default=-1)
    output_time = models.IntegerField(verbose_name="seconds", default=-1)
    output_time_unit = models.TextField(default="secs")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class F1FlowTestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="hw_hsu_test", choices=[(0, "hw_hsu_test")])
    input_iterations = models.IntegerField(default=-1)
    output_time = models.IntegerField(verbose_name="seconds", default=-1)
    output_time_unit = models.TextField(default="secs")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class BootTimePerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
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
    tag = "analytics"

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
    tag = "analytics"
    interpolation_allowed = models.BooleanField(default=True)
    interpolated = models.BooleanField(default=False)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class FunMagentPerformanceTest(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="fun_magent_perf_test", choices=[(0, "fun_magent_perf_test")])
    input_metric_name = models.CharField(max_length=40, default="fun_magent_rate_malloc_free_per_sec",
                                         choices=[(0, "fun_magent_rate_malloc_free_per_sec")])
    output_latency = models.IntegerField(verbose_name="KOps/sec", default=-1)
    output_latency_unit = models.TextField(default="Kops")


    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class WuStackSpeedTestPerformance(models.Model):
    interpolation_allowed = models.BooleanField(default=False)
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=30, default="wustack_speed_test", choices=[(0, "wustack_speed_test")])
    input_metric_name = models.CharField(max_length=40, default="wustack_alloc_free_cycles",
                                         choices=[(0, "wustack_alloc_free_cycles")])
    output_average = models.IntegerField(verbose_name="Alloc/free cycles average", default=-1)
    output_average_unit = models.TextField(default="cycles")
    tag = "analytics"

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s

class MileStoneMarkers(models.Model):
    metric_id = models.IntegerField(default=-1)
    milestone_date = models.DateTimeField(verbose_name="Date", default=datetime.now)
    milestone_name = models.TextField(default="")
    tag = "analytics"

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
'''
ANALYTICS_MAP = {
    "Performance1": {
        "model": Performance1,
        "module": "networking",
        "component": "general",
        "verbose_name": "Performance 1 ..."
    },
    "UnitTestPerformance": {
        "model": UnitTestPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "UnitTestPerformance"
    },

    "PerformanceBlt": {
        "model": PerformanceBlt,
        "module": "storage",
        "component": "general",
        "verbose_name": "Block Local Thin Performance"
    },

    "PerformanceIkv": {
        "model": PerformanceIkv,
        "module": "storage",
        "component": "general",
        "verbose_name": "IKV PUT Performance"
    },

    "VolumePerformance": {
        "model": VolumePerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "Volume Performance"
    },

    "AllocSpeedPerformance": {
        "model": AllocSpeedPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "Alloc Speed Performance"
    },

    "WuLatencyAllocStack": {
        "model": WuLatencyAllocStack,
        "module": "system",
        "component": "general",
        "verbose_name": "WU Latency Test: Alloc stack"
    },
    "WuLatencyUngated": {
        "model": WuLatencyUngated,
        "module": "system",
        "component": "general",
        "verbose_name": "WU Latency Test: Ungated"
    },
    "EcPerformance": {
        "model": EcPerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "EC Performance"

    },
    "BcopyPerformance": {
        "model": BcopyPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "BCopy Performance"
    },
    "BcopyFloodDmaPerformance": {
        "model": BcopyFloodDmaPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "BCopy Flood DMA Performance"
    },
    "JenkinsJobIdMap": {
        "model": JenkinsJobIdMap,
        "module": "system",
        "component": "general",
        "verbose_name": "Jenkids Job Id map"
    },
    "LsvZipCryptoPerformance": {
        "model": LsvZipCryptoPerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "LSV Zip Crypto Performance"
    },
    "EcVolPerformance": {
        "model": EcVolPerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "EC Vol Performance"
    },
    "NuTransitPerformance": {
        "model": NuTransitPerformance,
        "module": "networking",
        "component": "general",
        "verbose_name": "NU Transit Performance"
    },
    "VoltestPerformance": {
        "model": VoltestPerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "Voltest Performance"
    },
    "WuDispatchTestPerformance": {
        "model": WuDispatchTestPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "WU Dispatch Performance Test"
    },
    "WuSendSpeedTestPerformance": {
        "model": WuSendSpeedTestPerformance,
        "module": "system",
        "component": "general",
        "verbose_name": "WU Dispatch Performance Test"
    },
    "HuRawVolumePerformance": {
        "model": HuRawVolumePerformance,
        "module": "storage",
        "component": "general",
        "verbose_name": "HU Raw Volume Performance"
    },
    "FunMagentPerformanceTest": {
        "model": FunMagentPerformanceTest,
        "module": "system",
        "component": "general",
        "verbose_name": "Fun Magent Performance test"
    },
    "ShaxPerformance": {
        "model": ShaxPerformance,
        "module": "security",
        "component": "general",
        "verbose_name": "Shax Performance"
    }
}
'''
