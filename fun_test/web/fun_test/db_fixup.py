import os
import django
import json
import random
import re
from datetime import datetime, timedelta
from web.web_global import PRIMARY_SETTINGS_FILE
from fun_global import get_localized_time, get_current_time
from fun_settings import MAIN_WEB_APP
os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, ShaxPerformance
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import MetricChartStatus, MetricChartStatusSerializer
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

start_month = 4
start_day = 1
minute = 59
hour = 23
second = 59

def get_rounded_time(dt):
    rounded_d = datetime(year=dt.year, month=dt.month, day=dt.day, hour=hour, minute=minute, second=second)
    rounded_d = get_localized_time(rounded_d)
    return rounded_d

def get_day_bounds(dt):
    d = get_rounded_time(dt)
    start = d.replace(hour=0, minute=0, second=0)
    end = d.replace(hour=23, minute=59, second=59)
    return start, end

def get_entries_for_day(model, day, data_set):
    bounds = get_day_bounds(day)
    d = {}
    d["input_date_time__range"] = bounds
    inputs = data_set["inputs"]
    for input_name, input_value in inputs.iteritems():
        if d == "input_date_time":
            continue
        d[input_name] = input_value
    result = model.objects.filter(**d)
    return result

def get_first_record(model, data_set):
    inputs = data_set["inputs"]
    d = {}
    for input_name, input_value in inputs.iteritems():
        d[input_name] = input_value
    order_by = "-input_date_time"
    entries = model.objects.filter(**d).order_by(order_by)
    i = 0


def fixup_expected_values(chart, model, data_set):
    modified = 0
    first_record = get_first_record(model=model, data_set=data_set)
    if not first_record:
        i = 0
    else:
        first_record = first_record[-1]
        output_name = data_set["output"]["name"]
        if output_name in first_record:
            data_set["output"]["expected"] = first_record[output_name]
            modified = 1
        j = 0
        # data_set["expected"] = first_rec
    # self.data_sets = json.dumps(data_set)
    # self.save()
    return modified


def interpolate(chart, model, from_date, to_date):

    data_sets = json.loads(chart.data_sets)

    for data_set in data_sets:
        last_good_entry = None
        print "Current Data-set: {}".format(json.dumps(data_set))
        current_date = get_rounded_time(from_date)
        while current_date <= to_date:
            entries = get_entries_for_day(model=model, day=current_date, data_set=data_set)
            if len(entries):
                last_good_entry = entries[0]
            else:
                if last_good_entry:
                    print "Interpolating"
                    last_good_entry.pk = None
                    last_good_entry.interpolated = True
                    last_good_entry.input_date_time = current_date
                    last_good_entry.save()
            current_date = current_date + timedelta(days=1)
            # print current_date


def prepare_status(chart, purge_old_status=False):
    metric_id = chart.metric_id
    chart_name = chart.chart_name
    result = {}
    if purge_old_status:
        chart.score_cache_valid = False
        chart.save()
        entries = MetricChartStatus.objects.filter(chart_name=chart.chart_name, metric_id=chart.metric_id)
        entries.all().delete()
    if chart.chart_name == "LSV":
        j = 0
    # print "Preparing status for: {}".format(chart.chart_name)
    children = json.loads(chart.children)
    children_weights = json.loads(chart.children_weights)
    children_weights = {int(x): y for x, y in children_weights.iteritems()}
    data_sets = []
    valid_dates = []

    sum_of_child_weights = 0
    scores = {}

    result["num_build_failed"] = 0
    result["num_degrades"] = 0
    result["children_score_map"] = {}
    result["valid_dates"] = []
    today = datetime.now()

    from_date = datetime(year=today.year, month=start_month, day=start_day, minute=minute, hour=hour, second=second)

    yesterday = today - timedelta(days=0) # Just use today
    yesterday = get_rounded_time(yesterday)
    to_date = yesterday
    current_date = get_rounded_time(from_date)

    data_sets = chart.data_sets
    data_sets = json.loads(data_sets)

    if not chart.score_cache_valid:
        if not chart.leaf:
            print "Calculating container score for {}".format(chart.chart_name)
            for child in children:
                child_metric = MetricChart.objects.get(metric_id=child)
                child_result = prepare_status(chart=child_metric, purge_old_status=purge_old_status)
                child_result_scores = child_result["scores"]
                valid_dates = child_result["valid_dates"]
                # last_valid_date = child_valid_dates[-1]

                if child_result["scores"]:
                    result["children_score_map"][child_metric.metric_id] = child_result["scores"][to_date]

                child_last_build_status = child_result["last_build_status"]
                result["num_degrades"] += child_result["num_degrades"]
                result["num_build_failed"] += child_result["num_build_failed"]
                child_weight = children_weights[child] if child in children_weights else 1
                for date_time, child_score in child_result_scores.iteritems():

                    scores.setdefault(date_time, 0)
                    scores[date_time] += child_score * child_weight
                    print "Child: {} Score: {} Datetime: {}".format(child_metric.chart_name, child_score, date_time)
                sum_of_child_weights += child_weight

            # Normalize all scores
            for date_time, score in scores.iteritems():
                current_score = 0
                if sum_of_child_weights:
                    scores[date_time] /= sum_of_child_weights
                else:
                    scores[date_time] = 0
                mcs = MetricChartStatus(date_time=date_time,
                                        metric_id=metric_id,
                                        chart_name=chart_name,
                                        data_sets=data_sets,
                                        score=scores[date_time],
                                        children_score_map=result["children_score_map"])
                print "Chart: {} Date: {} Score: {}".format(chart.chart_name, date_time, scores[date_time])
                mcs.save()
        else:
            # print "Reached leaf: {}".format(chart.chart_name)

            model = app_config.get_metric_models()[chart.metric_model_name]
            if model.objects.first().interpolation_allowed:
                interpolate(model=model, from_date=from_date, to_date=to_date, chart=chart)

            last_good_score = 0
            penultimate_good_score = 0  # The good score before the previous good score
            current_score = 0

            replacement = False
            while current_date <= to_date:
                valid_dates.append(current_date)
                if current_score:  # Bertrand wanted to keep track of the last good score
                    penultimate_good_score = last_good_score
                    last_good_score = current_score

                # print current_date

                data_sets = data_sets
                children = json.loads(chart.children)
                children_weights = json.loads(chart.children_weights)
                children_weights = {int(x): y for x, y in children_weights.iteritems()}

                children_info = {}
                data_set_mofified = False
                data_sets = json.loads(chart.data_sets)

                if len(data_sets):
                    data_set_combined_goodness = 0
                    for data_set in data_sets:
                        if current_date > get_localized_time(datetime(year=2018, month=8, day=10)):
                            j = 0
                        # print "Processing data-set: {}".format(json.dumps(data_set))
                        entries = get_entries_for_day(model=model, day=current_date, data_set=data_set)
                        score = -1
                        this_days_record = None
                        if len(entries):
                            if len(entries) > 1:
                                this_days_record = entries.last()
                            else:
                                this_days_record = entries[0]

                            max_value = data_set["output"]["max"]
                            min_value = data_set["output"]["min"]
                            output_name = data_set["output"]["name"]  # TODO
                            if "expected" in data_set["output"]:
                                expected_value = data_set["output"]["expected"]
                            else:
                                # let's fix it up
                                print ("Fixing expected values")
                                data_set_mofified = data_set_mofified or chart.fixup_expected_values(
                                    data_set=data_set)
                                expected_value = max_value
                                if not chart.positive:
                                    expected_value = min_value
                            get_first_record(model=model, data_set=data_set)
                            output_value = getattr(this_days_record, output_name)

                            # data_set_statuses.append(leaf_status)
                            if expected_value is not None:
                                if chart.positive:
                                    data_set_combined_goodness += (float(
                                        output_value) / expected_value) * 100 if output_value >= 0 else 0
                                else:
                                    if output_value:
                                        data_set_combined_goodness += (float(
                                            expected_value) / output_value) * 100 if output_value >= 0 else 0
                                    else:
                                        print "ERROR: {}, {}".format(chart.chart_name,
                                                                     chart.metric_model_name)
                    current_score = round(data_set_combined_goodness / len(data_sets), 1)


                    # is_leaf_degrade = current_score < last_good_score
                    replacement = False
                    if current_score <= 0:
                        current_score = last_good_score
                        replacement = True
                        # is_leaf_degrade = penultimate_good_score > current_score

                    scores[current_date] = current_score

                if data_set_mofified:
                    chart.data_sets = json.dumps(data_sets)
                    chart.save()
                # print current_date, scores

                mcs = MetricChartStatus(date_time=current_date,
                                        metric_id=metric_id,
                                        chart_name=chart_name,
                                        data_sets=data_sets,
                                        score=current_score)
                mcs.save()
                current_date = current_date + timedelta(days=1)
                # current_date = get_localized_time(current_date)


            # print current_score, last_good_score

            is_leaf_degrade = current_score < last_good_score
            if replacement:
                is_leaf_degrade = current_score < penultimate_good_score
            if is_leaf_degrade or not current_score:
                result["num_degrades"] += 1


        result["scores"] = scores
        result["last_build_status"] = chart.last_build_status == "PASSED"
        result["valid_dates"] = valid_dates
        if not result["last_build_status"]:
            result["num_build_failed"] = 1
        if valid_dates:
            print "Chart: {} num_degrades: {}, last_score: {}".format(chart.chart_name, result["num_degrades"], result["scores"][valid_dates[-1]])
        if chart_name == "Networking":
            j = 0
        chart.save()
    else:
        date_range = [from_date, to_date]
        entries = MetricChartStatus.objects.filter(date_time__range=date_range,
                                                   chart_name=chart_name,
                                                   metric_id=metric_id)
        serialized = MetricChartStatusSerializer(entries, many=True)
        serialized_data = serialized.data[:]
        result["scores"] = {}
        for element in serialized_data:
            j = dict(element)
            result["scores"][j["date_time"]] = j

    # chart.last_build_status = result["last_build_status"]
    chart.score_cache_valid = True
    chart.last_num_degrades = result["num_degrades"]
    chart.last_status_update_date = get_current_time()
    chart.last_num_build_failed = result["num_build_failed"]
    chart.save()
    return result

if __name__ == "__main__":
    total_chart = MetricChart.objects.get(metric_model_name="MetricContainer", chart_name="Total")
    prepare_status(chart=total_chart, purge_old_status=True)


if __name__ == "__main2__":
    pass
