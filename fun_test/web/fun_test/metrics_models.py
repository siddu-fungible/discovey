from django.db import models
from rest_framework.serializers import ModelSerializer
import json
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

class MetricChart(models.Model):
    data_sets = models.TextField(default="[]")
    chart_name = models.TextField(unique=True)
    metric_model_name = models.TextField(default="Performance1")
    description = models.TextField(default="TBD")
    metric_id = models.IntegerField(default=10)
    children = models.TextField(default="[]")
    leaf = models.BooleanField(default=False)
    positive = models.BooleanField(default=True)

    def __str__(self):
        return "{} : {} : {}".format(self.chart_name, self.metric_model_name, self.metric_id)

    def get_children(self):
        return json.loads(self.children)

    def add_child(self, child_id):
        children = json.loads(self.children)
        children.append(child_id)
        self.children = json.dumps(children)
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

    def get_last_record(self):
        return self.filter(last=True)

    def get_status(self):
        status = False
        goodness = 0
        children = json.loads(self.children)
        if not self.leaf:
            if len(children):
                status = True
                for child in children:
                    child_metric = MetricChart.objects.get(metric_id=child)
                    child_status, child_goodness = child_metric.get_status()
                    status = status and child_status
                    goodness += child_goodness
        else:
            last_record = self.get_last_record()
            data_sets = json.loads(self.data_sets)
            if len(data_sets):
                data_set = data_sets[0]

                max_value = data_set["output"]["max"]
                min_value = data_set["output"]["min"]
                output_name = data_set["output"]["name"]
                expected_value = None
                if "expected" in data_set["output"]:
                    expected_value = data_set["output"]["expected"]
                else:
                    expected_value = max_value
                    if not self.positive:
                        expected_value = min_value

                output_value = last_record[output_name]
                status = output_value >= min_value and output_value <= max_value

                if expected_value is not None:
                    if self.positive:
                        goodness = (float(output_value) / expected_value) * 100
                    else:
                        goodness = (float(expected_value) / output_value) * 100
        print("Chart_name: {}, Status: {}, Goodness: {}".format(self.chart_name, status, goodness))
        return status, goodness

    def filter(self, last=False):
        data = []
        data_sets = json.loads(self.data_sets)
        if len(data_sets):
            data_set = data_sets[0]
            inputs = data_set["inputs"]
            model = ANALYTICS_MAP[self.metric_model_name]["model"]
            d = {}
            for input_name, input_value in inputs.iteritems():
                d[input_name] = input_value
            try:
                if not last:
                    entries = model.objects.filter(**d).order_by("-id")
                    for entry in entries:
                        data.append(model_to_dict(entry))
                else:
                    entry = model.objects.filter(**d).last()
                    data = model_to_dict(entry)

            except ObjectDoesNotExist:
                logger.critical("No data found Model: {} Inputs: {}".format(self.metric_model_name, str(inputs)))
        return data

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


class PerformanceBlt(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1_block_size = models.CharField(max_length=10, choices=[(0, "4K"), (1, "8K"), (2, "16K")], verbose_name="Block size")
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


class AllocSpeedPerformance(models.Model):
    key = models.CharField(max_length=30, verbose_name="Software date")
    input_app = models.TextField(verbose_name="alloc_speed_test", default="alloc_speed_test",  choices=[(0, "alloc_speed_test")])
    output_one_malloc_free_wu = models.IntegerField(verbose_name="Time in ns (WU)")
    output_one_malloc_free_threaded = models.IntegerField(verbose_name="Time in ns (Threaded)")
    tag = "analytics"

    def __str__(self):
        return "{}..{}..{}".format(self.key, self.output_one_malloc_free_wu, self.output_one_malloc_free_threaded)


class VolumePerformanceSerializer(ModelSerializer):
    class Meta:
        model = VolumePerformance
        fields = "__all__"


class AllocSpeedPerformanceSerializer(ModelSerializer):
    class Meta:
        model = AllocSpeedPerformance
        fields = "__all__"


ANALYTICS_MAP = {
    "Performance1": {
        "model": Performance1,
        "module": "networking",
        "component": "general",
        "verbose_name": "Performance 1 ..."
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
    }

}

