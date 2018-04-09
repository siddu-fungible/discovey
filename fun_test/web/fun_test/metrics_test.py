import os
import django
import json
import random
import logging
from web.web_global import PRIMARY_SETTINGS_FILE
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, LastMetricId
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)


def add_metric(metric_model_name, chart_name, data_sets=None, description="", positive=True, leaf=True):
    c = None
    if not data_sets:
        data_sets = "[]"

    else:
        data_sets = json.dumps(data_sets)
    try:
        c = MetricChart(metric_model_name=metric_model_name,
                        chart_name=chart_name,
                        data_sets=data_sets, metric_id=LastMetricId.get_next_id(),
                        positive=positive,
                        leaf=leaf)
        c.save()
    except Exception as ex:
        logger.critical(str(ex))
    return c

def delete_metric(metric_model_name, chart_name, metric_id):
    try:
        c = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=chart_name, metric_id=metric_id)
        c.delete()
        c.save()
    except ObjectDoesNotExist:
        pass
    return True

def get_metric_by_id(metric_id):
    result = None
    try:
        result = MetricChart.objects.get(metric_id=metric_id)
    except ObjectDoesNotExist:
        pass
    return result




if __name__ == "__main__":


    data_set = {
        "inputs": {
            "input1": "input1_0",
            "input2": "12"
        },
        "output": {
            "name": "output1",
            "min": 2,
            "max": 156,
            "expected": 55
        }
    }
    old_charts = ["root_chart", "child1chart", "child2chart"]
    for old_chart in old_charts:
        try:
            c = MetricChart.objects.filter(chart_name=old_chart)
            c.delete()
        except Exception as ex:
            pass
    metric_model_name = "Abc"
    chart_name = "root_chart"
    description = "root_desc"
    root_metric = add_metric(metric_model_name=metric_model_name,
                             chart_name=chart_name,
                             description=description,
                             data_sets=[data_set],
                             positive=False, leaf=False)


    # Child 1
    metric_model_name = "Performance1"
    chart_name = "child1chart"
    description = "child1description"
    child1 = add_metric(metric_model_name=metric_model_name, chart_name=chart_name, description=description, leaf=False)

    # Child 2
    metric_model_name = "child2"
    chart_name = "child2chart"
    description = "child2description"
    child2 = add_metric(metric_model_name=metric_model_name, chart_name=chart_name, description=description, leaf=False)

    root_metric = get_metric_by_id(metric_id=root_metric.metric_id)
    root_metric.add_child(child_id=child1.metric_id)
    root_metric.add_child(child_id=child2.metric_id)

    print root_metric.get_children()


    # Leaf 1
    leaf_charts = []
    for i in xrange(4):
        chart_name = "leaf_chart_{}".format(i)
        MetricChart.objects.filter(chart_name=chart_name).delete()
        metric_model_name = "Performance1"
        description = "leaf_chart_{}".format(i)
        leaf_charts.append(add_metric(metric_model_name=metric_model_name,
                                      chart_name=chart_name,
                                      description=description,
                                      leaf=True, data_sets=[data_set]))


    child1.add_child(child_id=leaf_charts[0].metric_id)
    child1.add_child(child_id=leaf_charts[1].metric_id)
    child2.add_child(child_id=leaf_charts[2].metric_id)
    child2.add_child(child_id=leaf_charts[3].metric_id)

    # records = root_metric.filter(last=True)
    # print records
    #for record in records:
    #    print str(record)
    # print leaf_charts[0].get_status()
    print root_metric.get_status()