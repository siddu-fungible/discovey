import django
import math
from web.web_global import PRIMARY_SETTINGS_FILE
from fun_global import *
from fun_settings import MAIN_WEB_APP
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart
from web.fun_test.metrics_models import MetricChartStatus, MetricChartStatusSerializer
from web.fun_test.metrics_models import MetricsGlobalSettings
from django.utils import timezone

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

start_year = 2018
start_month = 4
start_day = 1
minute = 59
hour = 23
second = 59

latency_category = ["nsecs", "usecs", "msecs", "secs"]
ops_category = ["ops", "Kops", "Mops", "Gops"]
operations_category = ["op", "Kop", "Mop", "Gop"]
cycles_category = ["cycles"]
bits_bytes_category = ["b", "B", "KB", "MB", "GB", "TB"]
bandwidth_category = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Bps", "KBps", "MBps", "GBps", "TBps"]
packets_per_sec_category = ["pps", "Mpps", "Kpps", "Gpps"]
connections_per_sec_category = ["cps", "Mcps", "Kcps", "Gcps"]
power_category = ["W", "kW", "MW", "mW"]


def get_rounded_time(dt):
    rounded_d = dt.replace(year=dt.year, month=dt.month, day=dt.day, hour=hour, minute=minute, second=0, microsecond=0)
    # rounded_d = datetime(year=dt.year, month=dt.month, day=dt.day, hour=hour, minute=minute, second=second)
    # rounded_d = get_localized_time(rounded_d)
    return rounded_d


def get_day_bounds(dt):
    d = get_rounded_time(dt)
    start = d.replace(hour=0, minute=0, second=0, year=dt.year)
    end = d.replace(hour=23, minute=59, second=59, year=dt.year)
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
    order_by = "-input_date_time"
    result = model.objects.filter(**d).order_by(order_by)
    return result


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


fixup_results_cache = {}


def get_tolerance():
    global_settings = MetricsGlobalSettings.objects.first()
    return global_settings.tolerance_percentage / 100


def prepare_status(chart, cache_valid, purge_old_status=False):
    if purge_old_status:
        chart.score_cache_valid = False
        chart.save()
        entries = MetricChartStatus.objects.filter(chart_name=chart.chart_name, metric_id=chart.metric_id)
        entries.all().delete()
    else:
        chart.score_cache_valid = False
        chart.save()

    result = {}

    if not chart.score_cache_valid:
        if not chart.leaf:
            calculate_container_scores(cache_valid=cache_valid, chart=chart, purge_old_status=purge_old_status,
                                       result=result)
        else:
            calculate_leaf_scores(cache_valid=cache_valid, chart=chart, result=result, from_log=False)

    else:
        set_result_dict(result=result)
        dates = set_from_to_dates(chart=chart)
        from_date = dates["from_date"]
        to_date = dates["to_date"]
        date_range = [from_date, to_date]
        entries = MetricChartStatus.objects.filter(date_time__range=date_range,
                                                   chart_name=chart.chart_name,
                                                   metric_id=chart.metric_id)
        serialized = MetricChartStatusSerializer(entries, many=True)
        serialized_data = serialized.data[:]
        result["scores"] = {}
        result["data_sets"] = chart.get_data_sets()
        for element in serialized_data:
            j = dict(element)
            result["scores"][j["date_time"]] = j
        set_chart_status_details(chart=chart, result=result)

    return result


def set_result_dict(result):
    result["num_build_failed"] = 0
    result["num_degrades"] = 0
    result["children_score_map"] = {}
    result["valid_dates"] = []
    result["num_leaves"] = 0
    result["last_good_score"] = -1
    result["penultimate_good_score"] = -1
    result["copied_score"] = False
    result["copied_score_disposition"] = 0


def set_from_to_dates(chart):
    dates = {}
    # calculate the from date and to date for fetching the data
    today = datetime.datetime.now(pytz.timezone('US/Pacific'))
    from_date = chart.base_line_date
    from_date = adjust_timezone_for_day_light_savings(from_date)
    from_date = get_rounded_time(from_date)
    yesterday = today  # - timedelta(days=0) # Just use today
    yesterday = get_rounded_time(yesterday)
    to_date = yesterday
    dates["from_date"] = from_date
    dates["to_date"] = to_date
    return dates


def set_chart_status_details(chart, result):
    # chart.last_build_status = result["last_build_status"]
    chart_status_entries = MetricChartStatus.objects.filter(metric_id=chart.metric_id).order_by('-date_time')[:2]
    if chart_status_entries:
        chart_status_entries[0].suite_execution_id = chart.last_suite_execution_id
        chart_status_entries[0].jenkins_job_id = chart.last_jenkins_job_id
        chart_status_entries[0].test_case_id = chart.last_test_case_id
        chart_status_entries[0].lsf_job_id = chart.last_lsf_job_id
        chart_status_entries[0].build_status = chart.last_build_status
        chart_status_entries[0].git_commit = chart.last_git_commit
        chart_status_entries[0].save()
        result["last_good_score"] = chart_status_entries[0].score
        if (len(chart_status_entries) >= 2):
            result["penultimate_good_score"] = chart_status_entries[1].score
        else:
            result["penultimate_good_score"] = chart_status_entries[0].score
        result["copied_score_disposition"] = chart_status_entries[0].copied_score_disposition
        result["copied_score"] = chart_status_entries[0].copied_score
    chart.score_cache_valid = True
    chart.last_num_degrades = result["num_degrades"]
    chart.last_status_update_date = get_current_time()
    chart.last_num_build_failed = result["num_build_failed"]
    chart.num_leaves = result["num_leaves"]
    chart.last_good_score = result["last_good_score"]
    chart.penultimate_good_score = result["penultimate_good_score"]
    chart.copied_score = result["copied_score"]
    chart.copied_score_disposition = result["copied_score_disposition"]
    chart.data_sets = json.dumps(result["data_sets"])
    chart.save()


def adjust_timezone_for_day_light_savings(current_date):
    date_time_obj = datetime.datetime(year=current_date.year, month=current_date.month, day=current_date.day,
                                      hour=current_date.hour, second=current_date.second, minute=current_date.minute)
    return get_localized_time(date_time_obj)

def _is_valid_output(output_value):
    return (output_value != -1 and not math.isinf(output_value))

def _update_best_value(current_value, best_value_dict, chart, data_set):
    if (chart.positive and current_value > best_value_dict[data_set["name"]]):
        best_value_dict[data_set["name"]] = current_value
    elif (not chart.positive and current_value < best_value_dict[data_set["name"]]):
        best_value_dict[data_set["name"]] = current_value

def calculate_leaf_scores(cache_valid, chart, result, from_log=False):
    # print "Reached leaf: {}".format(chart.chart_name)
    set_result_dict(result=result)
    dates = set_from_to_dates(chart=chart)
    from_date = dates["from_date"]
    to_date = dates["to_date"]
    scores = {}
    valid_dates = []
    current_date = get_rounded_time(from_date)
    model = app_config.get_metric_models()[chart.metric_model_name]
    if model.objects.first() and model.objects.first().interpolation_allowed:
        interpolate(model=model, from_date=from_date, to_date=to_date, chart=chart)

    last_good_score = 0
    penultimate_good_score = 0  # The good score before the previous good score
    current_score = 0
    is_leaf_degrade = False
    replacement = False
    if from_log:
        print "from_log"
    else:
        if cache_valid:
            entries = MetricChartStatus.objects.filter(metric_id=chart.metric_id).order_by("date_time")
            if len(entries):
                last_entry = entries.last()
                last_date = last_entry.date_time
                last_good_score = chart.last_good_score
                penultimate_good_score = chart.penultimate_good_score
                for entry in entries:
                    valid_dates.append(entry.date_time)
                    scores[entry.date_time] = entry.score
                current_date = last_date
                current_date = timezone.localtime(current_date)
                current_date = adjust_timezone_for_day_light_savings(current_date)
        data_set_mofified = False
        data_sets = json.loads(chart.data_sets)
        num_data_sets_with_expected = 0
        for data_set in data_sets:
            if "reference" in data_set["output"]:
                reference_value = data_set["output"]["reference"]
                if not reference_value or reference_value <= 0:
                    data_set_mofified = chart.fixup_reference_values(
                        data_set=data_set)
            else:
                # let's fix it up
                print ("Fixing reference values")
                data_set_mofified = chart.fixup_reference_values(
                    data_set=data_set)
            if "expected" in data_set["output"]:
                if data_set["output"]["expected"] and data_set["output"]["expected"] >= 0:
                    num_data_sets_with_expected += 1
        if data_set_mofified:
            chart.data_sets = json.dumps(data_sets)
            chart.save()
        num_data_sets_with_expected = len(
            data_sets) if num_data_sets_with_expected == 0 else num_data_sets_with_expected
        data_sets = json.loads(chart.data_sets)
        best_value_dict = {}
        for data_set in data_sets:
            best_value_dict[data_set["name"]] = -1
        while current_date <= to_date:
            result["num_degrades"] = 0
            valid_dates.append(current_date)
            if len(data_sets):
                data_set_combined_goodness = 0
                for data_set in data_sets:
                    expected_value = data_set["output"]["expected"] if "expected" in data_set["output"] else -1
                    if num_data_sets_with_expected == len(data_sets) or (expected_value and expected_value != -1):
                        entries = get_entries_for_day(model=model, day=current_date, data_set=data_set)
                        if len(entries):
                            this_days_record = entries.first()
                            output_name = data_set["output"]["name"]  # TODO
                            output_unit = output_name + "_unit"
                            reference_value = data_set["output"]["reference"]
                            output_value = getattr(this_days_record, output_name)
                            _update_best_value(current_value=output_value, best_value_dict=best_value_dict,
                                                chart=chart, data_set=data_set)
                            if hasattr(this_days_record, output_unit):
                                output_unit = getattr(this_days_record, output_unit)
                            else:
                                output_unit = None
                            if output_value and _is_valid_output(output_value):
                                output_value = convert_to_base_unit(output_value=output_value, output_unit=output_unit)

                            # data_set_statuses.append(leaf_status)
                            if reference_value is not None:
                                if expected_value and expected_value != -1:
                                    reference_value = expected_value
                                if output_unit:
                                    reference_value = convert_to_base_unit(output_value=reference_value,
                                                                           output_unit=data_set["output"]["unit"])
                                if output_value and _is_valid_output(output_value):
                                    if chart.positive:
                                        data_set_combined_goodness += (float(
                                            output_value) / reference_value) * 100 if output_value >= 0 and \
                                                                                      reference_value >= 0 else 0
                                    else:
                                        data_set_combined_goodness += (float(
                                            reference_value) / output_value) * 100 if output_value >= 0 and \
                                                                                      reference_value >= 0 else 0
                                else:
                                    print "ERROR: {}, {}".format(chart.chart_name, chart.metric_model_name)
                current_score = round(data_set_combined_goodness / num_data_sets_with_expected,
                                      1) if num_data_sets_with_expected != 0 else 0

                # is_leaf_degrade = current_score < last_good_score
                replacement = False
                if current_score <= 0:
                    current_score = last_good_score
                    replacement = True
                    # is_leaf_degrade = penultimate_good_score > current_score

                if not replacement:  # Bertrand wanted to keep track of the last good score
                    if last_good_score:
                        penultimate_good_score = last_good_score
                    is_leaf_degrade = current_score < (last_good_score * (1 - get_tolerance()))
                    last_good_score = current_score
                else:
                    is_leaf_degrade = current_score < (penultimate_good_score * (1 - get_tolerance()))

                scores[current_date] = current_score

            chart_status = MetricChartStatus.objects.filter(date_time=current_date, metric_id=chart.metric_id)
            if not chart_status:
                mcs = MetricChartStatus(date_time=current_date,
                                        metric_id=chart.metric_id,
                                        chart_name=chart.chart_name,
                                        data_sets=data_sets,
                                        score=current_score)
                if replacement:
                    mcs.copied_score = True
                    mcs.copied_score_disposition = 0
                    if current_score > penultimate_good_score:
                        if current_score > (penultimate_good_score * (1 + get_tolerance())):
                            mcs.copied_score_disposition = 1
                    elif current_score < penultimate_good_score:
                        if current_score < (penultimate_good_score * (1 - get_tolerance())):
                            mcs.copied_score_disposition = -1
                    else:
                        mcs.copied_score_disposition = 0
                mcs.save()
            else:
                if replacement:
                    chart_status[0].copied_score = True
                    chart_status[0].copied_score_disposition = 0
                    if current_score > penultimate_good_score:
                        if current_score > (penultimate_good_score * (1 + get_tolerance())):
                            chart_status[0].copied_score_disposition = 1
                    elif current_score < penultimate_good_score:
                        if current_score < (penultimate_good_score * (1 - get_tolerance())):
                            chart_status[0].copied_score_disposition = -1
                    else:
                        chart_status[0].copied_score_disposition = 0
                else:
                    chart_status[0].copied_score = False
                    chart_status[0].copied_score_disposition = 0
                chart_status[0].score = current_score
                chart_status[0].data_sets = data_sets
                chart_status[0].save()

            if is_leaf_degrade or not current_score:
                result["num_degrades"] = 1
            current_date = current_date + timedelta(days=1)
            current_date = adjust_timezone_for_day_light_savings(current_date)
        for data_set in data_sets:
            data_set["output"]["best"] = best_value_dict[data_set["name"]]
        result["scores"] = scores
        result["last_build_status"] = chart.last_build_status == "PASSED"
        result["valid_dates"] = valid_dates
        result["data_sets"] = data_sets
        if not result["last_build_status"]:
            result["num_build_failed"] = 1
        valid_dates = result["valid_dates"]
        if valid_dates:
            print "Chart: {} num_degrades: {}, last_score: {}, num_leaves: {}".format(chart.chart_name,
                                                                                      result["num_degrades"],
                                                                                      result["scores"][valid_dates[-1]],
                                                                                      result["num_leaves"])
        print "Leaf Chart: {} num_degrades: {} score: {} penultimate_score: {} build date: {}".format(chart.chart_name,
                                                                                                      result[
                                                                                                          "num_degrades"],
                                                                                                      chart.last_good_score,
                                                                                                      chart.penultimate_good_score,
                                                                                                      chart.last_build_date)
        set_chart_status_details(chart=chart, result=result)


def calculate_container_scores(chart, purge_old_status, cache_valid, result):
    set_result_dict(result)
    dates = set_from_to_dates(chart=chart)
    to_date = dates["to_date"]
    scores = {}
    valid_dates = []
    children = json.loads(chart.children)
    children_weights = json.loads(chart.children_weights)
    children_weights = {int(x): y for x, y in children_weights.iteritems()}
    sum_of_child_weights = 0
    data_sets = []
    data_sets = json.loads(chart.data_sets)
    print "Calculating container score for {}".format(chart.chart_name)
    for child in children:

        child_metric = MetricChart.objects.get(metric_id=child)
        if child_metric.metric_id not in fixup_results_cache:
            temp_result = prepare_status(chart=child_metric, purge_old_status=purge_old_status, cache_valid=cache_valid)
            fixup_results_cache[child_metric.metric_id] = temp_result
        child_result = fixup_results_cache[child_metric.metric_id]

        if child_metric.chart_name != "All metrics":
            if child_metric.leaf:
                result["num_leaves"] += 1
            else:
                if chart.chart_name == "F1" or chart.chart_name == "S1":
                    print "XXXX Child: chart Name: {}, num_leaves: {}".format(child_metric.chart_name,
                                                                              child_result["num_leaves"])
                result["num_leaves"] += child_result["num_leaves"]

        child_result_scores = child_result["scores"]
        valid_dates = child_result["valid_dates"]
        # last_valid_date = child_valid_dates[-1]

        if child_result["scores"]:
            result["children_score_map"][child_metric.metric_id] = child_result["scores"][to_date]

        child_last_build_status = child_result["last_build_status"]
        if child_metric.chart_name == "All metrics":
            child_weight = 0
        else:
            child_weight = children_weights[child] if child in children_weights else 1
            result["num_degrades"] += child_result["num_degrades"]
            result["num_build_failed"] += child_result["num_build_failed"]
        for date_time, child_score in child_result_scores.iteritems():
            scores.setdefault(date_time, 0)
            scores[date_time] += child_score * child_weight
            # print "Child: {} Score: {} Datetime: {}".format(child_metric.chart_name, child_score, date_time)
        sum_of_child_weights += child_weight

    # Normalize all scores
    for date_time, score in scores.iteritems():
        current_score = 0
        if sum_of_child_weights:
            scores[date_time] /= sum_of_child_weights
        else:
            scores[date_time] = 0
        chart_status = MetricChartStatus.objects.filter(date_time=date_time, metric_id=chart.metric_id)
        if not chart_status:
            mcs = MetricChartStatus(date_time=date_time,
                                    metric_id=chart.metric_id,
                                    chart_name=chart.chart_name,
                                    data_sets=data_sets,
                                    score=scores[date_time],
                                    children_score_map=result["children_score_map"])
            # print "Chart: {} Date: {} Score: {}".format(chart.chart_name, date_time, scores[date_time])
            mcs.save()
        else:
            chart_status[0].score = scores[date_time]
            chart_status[0].children_score_map = result["children_score_map"]
            chart_status[0].data_sets = data_sets
            chart_status[0].save()
    result["scores"] = scores
    result["last_build_status"] = chart.last_build_status == "PASSED"
    result["valid_dates"] = valid_dates
    result["data_sets"] = chart.get_data_sets()
    if not result["last_build_status"]:
        result["num_build_failed"] = 1
    valid_dates = result["valid_dates"]
    if valid_dates:
        print "Chart: {} num_degrades: {}, last_score: {}, num_leaves: {}".format(chart.chart_name,
                                                                                  result["num_degrades"],
                                                                                  result["scores"][valid_dates[-1]],
                                                                                  result["num_leaves"])
    set_chart_status_details(chart=chart, result=result)


def convert_to_base_unit(output_value, output_unit):
    if output_unit:
        if output_unit in latency_category:
            if output_unit == "usecs":
                output_value = float(output_value / math.pow(10, 6))
            elif output_unit == "msecs":
                output_value = float(output_value / math.pow(10, 3))
            elif output_unit == "nsecs":
                output_value = float(output_value / math.pow(10, 9))
        elif output_unit in bandwidth_category:
            if output_unit == "Gbps":
                output_value = float(output_value * math.pow(10, 9))
            elif output_unit == "Tbps":
                output_value = float(output_value * math.pow(10, 12))
            elif output_unit == "Mbps":
                output_value = float(output_value * math.pow(10, 6))
            elif output_unit == "Kbps":
                output_value = float(output_value * math.pow(10, 3))
            elif output_unit == "GBps":
                output_value = float(output_value * 8 * math.pow(10, 9))
            elif output_unit == "TBps":
                output_value = float(output_value * 8 * math.pow(10, 12))
            elif output_unit == "MBps":
                output_value = float(output_value * 8 * math.pow(10, 6))
            elif output_unit == "KBps":
                output_value = float(output_value * 8 * math.pow(10, 3))
            elif output_unit == "Bps":
                output_value = float(output_value * 8)
        elif output_unit in bits_bytes_category:
            if output_unit == "GB":
                output_value = float(output_value * 8 * math.pow(10, 9))
            elif output_unit == "B":
                output_value = float(output_value * 8)
            elif output_unit == "KB":
                output_value = float(output_value * 8 * math.pow(10, 3))
            elif output_unit == "MB":
                output_value = float(output_value * 8 * math.pow(10, 6))
            elif output_unit == "TB":
                output_value = float(output_value * 8 * math.pow(10, 12))
        elif output_unit in ops_category:
            if output_unit == "Kops":
                output_value = float(output_value * math.pow(10, 3))
            elif output_unit == "Mops":
                output_value = float(output_value * math.pow(10, 6))
            elif output_unit == "Gops":
                output_value = float(output_value * math.pow(10, 9))
        elif output_unit in operations_category:
            if output_unit == "Kop":
                output_value = float(output_value * math.pow(10, 3))
            elif output_unit == "Mop":
                output_value = float(output_value * math.pow(10, 6))
            elif output_unit == "Gop":
                output_value = float(output_value * math.pow(10, 9))
        elif output_unit in packets_per_sec_category:
            if output_unit == "Mpps":
                output_value = float(output_value * math.pow(10, 6))
            if output_unit == "Kpps":
                output_value = float(output_value * math.pow(10, 3))
            if output_unit == "Gpps":
                output_value = float(output_value * math.pow(10, 9))
        elif output_unit in connections_per_sec_category:
            if output_unit == "Mcps":
                output_value = float(output_value * math.pow(10, 6))
            if output_unit == "Kcps":
                output_value = float(output_value * math.pow(10, 3))
            if output_unit == "Gcps":
                output_value = float(output_value * math.pow(10, 9))
        elif output_value in power_category:
            if output_unit == "kW":
                output_value = float(output_value * math.pow(10, 3))
            if output_unit == "MW":
                output_value = float(output_value * math.pow(10, 6))
            if output_unit == "mW":
                output_value = float(output_value / math.pow(10, 3))
    return output_value


if __name__ == "__main__":
    chart_names = ["F1", "S1", "All metrics"]
    for chart_name in chart_names:
        total_chart = MetricChart.objects.get(metric_model_name="MetricContainer", chart_name=chart_name)
        prepare_status(chart=total_chart, purge_old_status=False, cache_valid=False)
