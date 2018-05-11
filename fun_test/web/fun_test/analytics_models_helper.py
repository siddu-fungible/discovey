import os
import django
import json
import random
from web.web_global import PRIMARY_SETTINGS_FILE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance, WuLatencyAllocStack
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

    def add_entry(self, **kwargs):
        inputs = {}
        if "key" in kwargs:
            inputs["key"] = kwargs["key"]
        outputs = {}
        for key, value in kwargs.iteritems():
            if key.startswith("input_"):
                inputs[key] = value
            elif key.startswith("output_"):
                outputs[key] = value
        try:
            o = self.model.objects.get(**inputs)
            for k, v in outputs.iteritems():
                if hasattr(o, k):
                    setattr(o, k, v)
            o.save()
        except ObjectDoesNotExist:
            o = self.model(**kwargs)
            o.save()

    def get_entry(self, **kwargs):
        result = None
        inputs = {}
        if "key" in inputs:
            inputs["key"] = kwargs["key"]
        outputs = {}
        for key, value in kwargs.iteritems():
            if key.startswith("input_"):
                inputs[key] = value
        try:
            result = self.model.objects.get(**inputs)
        except ObjectDoesNotExist:
            pass
        return result

    def get_recent_entry(self):
        return self.model.objects.last()

class MetricChartHelper(object):
    def __init__(self, chart_name, metric_model_name):
        self.chart_name = chart_name
        self.metric_model_name = metric_model_name
        self.chart = MetricChart.objects.get(chart_name=chart_name, metric_model_name=metric_model_name)

    def set_output_data_set(self, output_name, min_value, max_value):
        data_sets = json.loads(self.chart.data_sets)
        for data_set in data_sets:
            if data_set["output"]["name"] == output_name:
                data_set["output"]["min"] = min_value
                data_set["output"]["max"] = max_value
                break

    def get_output_data_set(self, output_name):
        result = {}
        data_sets = json.loads(self.chart.data_sets)
        for data_set in data_sets:
            if data_set["output"]["name"] == output_name:
                result["min"] = data_set["output"]["min"]
                result["max"] = data_set["output"]["max"]
                break
        return result


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


class VolumePerformanceHelper(MetricHelper):
    model = VolumePerformance

    def __init__(self):
        super(VolumePerformanceHelper, self).__init__(model=self.model)

    def add_entry(self, key, volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw, write_latency, read_latency):
        try:
            entry = VolumePerformance.objects.get(key=key,
                                                  input_volume=volume,
                                                  input_test=test,
                                                  input_block_size=block_size,
                                                  input_io_depth=io_depth,
                                                  input_size=size,
                                                  input_operation=operation)
            entry.output_write_iops = write_iops
            entry.output_read_iops = read_iops
            entry.output_write_bw = write_bw
            entry.output_read_bw = read_bw
            entry.output_write_latency = write_latency
            entry.output_read_latency = read_latency
            entry.save()
        except ObjectDoesNotExist:
            pass
            one_entry = VolumePerformance(key=key,
                                          input_volume=volume,
                                          input_test=test,
                                          input_block_size=block_size,
                                          input_io_depth=io_depth,
                                          input_size=size,
                                          input_operation=operation,
                                          output_write_iops=write_iops,
                                          output_read_iops=read_iops,
                                          output_write_bw=write_bw,
                                          output_read_bw=read_bw,
                                          output_write_latency=write_latency,
                                          output_read_latency=read_latency)
            one_entry.save()


class AllocSpeedPerformanceHelper(MetricHelper):
    model = AllocSpeedPerformance

    def __init__(self):
        super(AllocSpeedPerformanceHelper, self).__init__(model=self.model)

    def add_entry(self, key, input_app, output_one_malloc_free_wu, output_one_malloc_free_threaded):
        try:
            entry = AllocSpeedPerformance.objects.get(key=key, input_app=input_app)
            entry.output_one_malloc_free_wu = output_one_malloc_free_wu
            entry.output_one_malloc_free_threaded = output_one_malloc_free_threaded
            entry.save()
        except ObjectDoesNotExist:
            pass
            one_entry = AllocSpeedPerformance(key=key,
                                              input_app=input_app,
                                              output_one_malloc_free_wu=output_one_malloc_free_wu,
                                              output_one_malloc_free_threaded=output_one_malloc_free_threaded)
            one_entry.save()

class WuLatencyAllocStackHelper(MetricHelper):
    model = WuLatencyAllocStack

    def __init__(self):
        super(WuLatencyAllocStackHelper, self).__init__(model=self.model)

    def add_entry(self, key, input_date_time, input_app, output_min, output_avg, output_max):
        entry = WuLatencyAllocStack



if __name__ == "__main__":
    AllocSpeedPerformanceHelper().clear()
if __name__ == "__main2__":
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
                metric_model_name="Performance1").save()

    builds = xrange(10)

    PerformanceBlt.objects.all().delete()
    PerformanceIkv.objects.all().delete()

    r = random.Random()
    r.seed("test")

    # Generate data for PerformanceBlt
    for build in builds:
        block_sizes = ["4K", "8K", "16K"]
        modes = ["Read", "Read-Write"]
        for block_size in block_sizes:
            for mode in modes:
                iops = r.randint(0, 100)
                bw = r.randint(0, 200)
                latency = r.randint(0, 300)
                p = PerformanceBlt(key=build, input1_block_size=block_size, input2_mode=mode, output1_iops=iops, output2_bw=bw, output3_latency=latency)
                p.save()

    # Prepare charts
    data_set1 = {"inputs": {
        "input1_block_size": "4K",
        "input2_mode": "Read"
    },
        "output": {
            "name": "output1_iops",
            "min": 0,
            "max": 85
        },
        "name": "Block-size:4K Mode: Read"
    }
    data_set2 = {"inputs": {
        "input1_block_size": "8K",
        "input2_mode": "Read"
    },
        "output": {
            "name": "output1_iops",
            "min": 0,
            "max": 75
        },
        "name": "Block-size:8K Mode: Read"
    }
    data_set3 = {"inputs": {
        "input1_block_size": "8K",
        "input2_mode": "Read-Write"
    },
        "output": {
            "name": "output1_iops",
            "min": 0,
            "max": 75
        },
        "name": "Block-size:8K Mode: Read-Write"
    }

    MetricChart(chart_name="BLT Performance IOPS", data_sets=json.dumps([data_set1, data_set2, data_set3]),
                metric_model_name="PerformanceBlt").save()

    data_set1 = {"inputs": {
        "input1_block_size": "4K",
        "input2_mode": "Read"
    },
        "output": {
            "name": "output3_latency",
            "min": 0,
            "max": 85
        },
        "name": "Block-size:4K Mode: Read"
    }

    data_set3 = {"inputs": {
        "input1_block_size": "8K",
        "input2_mode": "Read-Write"
    },
        "output": {
            "name": "output3_latency",
            "min": 0,
            "max": 75
        },
        "name": "Block-size:8K Mode: Read-Write"
    }

    MetricChart(chart_name="BLT Performance Latency", data_sets=json.dumps([data_set1, data_set3]),
                metric_model_name="PerformanceBlt").save()

    # Generate data for PerformanceIkv
    for build in builds:
        put_value_sizes = [4096, 8192]
        for put_value_size in put_value_sizes:
            output1_put_per_seccond = r.randint(0, 300)
            p = PerformanceIkv(key=build, input1_put_value_size=put_value_size, output1_put_per_seccond=output1_put_per_seccond)
            p.save()

    # Prepare charts
    data_set1 = {"inputs": {
        "input1_put_value_size": 4096,
    },
        "output": {
            "name": "output1_put_per_seccond",
            "min": 0,
            "max": 275
        },
        "name": "PUT Value size: 4096"
    }
    data_set2 = {"inputs": {
        "input1_put_value_size": 8192,
    },
        "output": {
            "name": "output1_put_per_seccond",
            "min": 0,
            "max": 275
        },
        "name": "PUT Value size: 8192"
    }

    MetricChart(chart_name="IKV Performance", data_sets=json.dumps([data_set1, data_set2]),
                metric_model_name="PerformanceIkv").save()

    # MetricChart(chart_name="Chart 2", data_sets=json.dumps([data_set3]), metric_model_name="Performance1").save()
