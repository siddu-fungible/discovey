import os
import django
import json
from web.web_global import PRIMARY_SETTINGS_FILE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart


class MetricHelper(object):
    def __init__(self, model):
        self.model = model

    def delete(self, key):
        entries = self.model.objects.filter(key=key)
        for entry in entries:
            entry.delete()
            entry.save()

    def clear(self):
        self.model.objects.all().delete()


class Performance1Helper(MetricHelper):
    model = Performance1

    def __init__(self):
        super(Performance1Helper, self).__init__(model=self.model)

    def add_entry(self, key, input1, input2, output1, output2, output3):
        one_entry = Performance1(key=key,
                                 input1=input1,
                                 input2=input2,
                                 output1=output1,
                                 output2=output2,
                                 output3=output3)
        one_entry.save()


if __name__ == "__main__":
    # MetricChart.objects.all().delete()

    performance1_helper = Performance1Helper()
    performance1_helper.clear()
    performance1_helper.add_entry(key="123", input1="input1_0", input2=12, output1=34, output2=56, output3="output3_1")
    performance1_helper.add_entry(key="143", input1="input1_0", input2=12, output1=56, output2=56, output3="output3_1")
    performance1_helper.add_entry(key="156", input1="input1_0", input2=12, output1=56, output2=56, output3="output3_1")

    performance1_helper.add_entry(key="123", input1="input1_1", input2=12, output1=67, output2=71, output3="output3_2")
    performance1_helper.add_entry(key="143", input1="input1_1", input2=12, output1=97, output2=71, output3="output3_2")
    performance1_helper.add_entry(key="156", input1="input1_1", input2=12, output1=12, output2=71, output3="output3_2")

    output_info = {
        "name": "output1",
        "min": 0,
        "max": 100
    }
    data_set1 = {"inputs": {
        "input1": "input1_0",
        "input2": 12
    },
        "output": {
            "name": "output1",
            "min": 0,
            "max": 100
        },
        "name": "data-set1"
    }
    data_set2 = {"inputs": {
        "input1": "input1_1",
        "input2": 12
    },
        "output": {
            "name": "output1",
            "min": 0,
            "max": 100
        },
        "name": "data-set2"
    }
    data_set3 = {"inputs": {
        "input1": "input1_1",
        "input2": "input2_1"
    },
        "output": {
            "name": "output1",
            "min": 0,
            "max": 100
        }
    }
    MetricChart.objects.all().delete()
    MetricChart(chart_name="Chart 1", data_sets=json.dumps([data_set1, data_set2]),
                metric_model_name="Performance1", module="networking").save()
    # MetricChart(chart_name="Chart 2", data_sets=json.dumps([data_set3]), metric_model_name="Performance1").save()
