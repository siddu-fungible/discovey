from django.db import models
from fun_global import RESULTS, get_current_time, get_localized_time
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
import json
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
import logging
from datetime import datetime, timedelta
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
    y1_axis_title = models.TextField(default="")
    y2_axis_title = models.TextField(default="")
    children_weights = models.TextField(default="{}")
    goodness_cache = models.TextField(default="[]")
    goodness_cache_range = models.IntegerField(default=5)
    goodness_cache_valid = models.BooleanField(default=False)
    status_cache = models.TextField(default="[]")

    def __str__(self):
        return "{} : {} : {}".format(self.chart_name, self.metric_model_name, self.metric_id)

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

    def get_entries_for_day(self, metric, day):
        bounds = self.get_day_bounds(day)
        result = metric.objects.filter(input_date_time__range=bounds)
        # if result.count() > 1:
        #    result = result.last()
        return result

    def fixup(self, metric, from_date, to_date):
        current_date = self.get_rounded_time(to_date)
        holes = {}
        day_entries = None

        while current_date >= from_date:
            entry = self.get_entries_for_day(metric=metric, day=current_date)

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
                        day_entries = self.get_entries_for_day(metric=metric, day=day)
                        if day_entries.count():
                            for day_entry in day_entries:
                                day_entry.pk = None
                                day_entry.interpolated = True
                                day_entry.input_date_time = current_date
                                day_entry.save()
                            break
                        else:
                            holes[self.get_rounded_time(day)] = False
                        i = i + 1
            else:
                day_entries = None
            current_date = current_date - timedelta(days=1)  # TODO: if we know the holes jump to the next hole




    def get_status(self, number_of_records=5):

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
        if self.chart_name == "Filter":
            j = 2
        if not self.leaf:
            if len(children):
                child_degrades = 0
                for child in children:
                    child_metric = MetricChart.objects.get(metric_id=child)
                    get_status = child_metric.get_status(number_of_records=number_of_records)
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

                        child_weight = children_weights[child] if child in children_weights else 1
                        goodness_values[i] += child_goodness_values[i] * child_weight
                        children_goodness_map[child] = child_goodness_values

        else:
            if self.goodness_cache_valid and (number_of_records == self.goodness_cache_range):
                goodness_values.extend(json.loads(self.goodness_cache))
                status_values.extend(json.loads(self.status_cache))
            else:
                leaf_status = True

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
                            if last_records and (last_records[-1]["status"] == RESULTS["FAILED"]):
                                leaf_status = False
                        except:
                            pass

                    for day_index in range(number_of_records - 1):
                        data_set_combined_goodness = 0
                        for data_set_index, data_set in enumerate(data_sets):

                            if last_records_map[data_set_index]["records"]:
                                try:
                                    this_days_record = last_records_map[data_set_index]["records"][day_index]
                                except:
                                    pass
                                max_value = data_set["output"]["max"]
                                min_value = data_set["output"]["min"]
                                try:
                                    output_name = data_set["output"]["name"]   #TODO
                                except:
                                    pass
                                if "expected" in data_set["output"]:
                                    expected_value = data_set["output"]["expected"]
                                else:
                                    expected_value = max_value
                                    if not self.positive:
                                        expected_value = min_value
                                output_value = this_days_record[output_name]

                                data_set_statuses.append(leaf_status)
                                if expected_value is not None:
                                    if self.positive:
                                        data_set_combined_goodness += (float(output_value) / expected_value) * 100
                                    else:
                                        if output_value:
                                            data_set_combined_goodness += (float(expected_value) / output_value) * 100
                                        else:
                                            print "ERROR: {}, {}".format(self.chart_name,
                                                                             self.metric_model_name)
                        # data_set_combined_goodness = round(data_set_combined_goodness, 1)
                        goodness_values.append(round(data_set_combined_goodness/len(data_sets), 1))

                    if data_set_statuses:
                        status_values.append(reduce(lambda x, y: x and y, data_set_statuses))
                    else:
                        status_values.append(True)  # Some data-sets may not exist


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
        print("Chart_name: {}, Status: {}, Goodness: {}".format(self.chart_name, status_values, goodness_values))
        self.goodness_cache = json.dumps(goodness_values)
        self.goodness_cache_valid = True
        self.goodness_cache_range = number_of_records
        self.status_cache = json.dumps(status_values)
        self.save()
        try:
            if goodness_values[-2] > goodness_values[-1]:
                num_degrades += 1
        except:
            num_degrades = 0
        return {"status_values": status_values,
                "goodness_values": goodness_values,
                "children_goodness_map": children_goodness_map,
                "num_children_passed": num_children_passed,
                "num_children_failed": num_children_failed,
                "num_degrades": num_degrades,
                "num_child_degrades": num_child_degrades}

    def filter(self, number_of_records=1, data_set=None):
        data = []
        # data_sets = json.loads(self.data_sets)
        if data_set:
            # data_set = data_sets[0]
            inputs = data_set["inputs"]
            model = ANALYTICS_MAP[self.metric_model_name]["model"]
            today = get_current_time()
            yesterday = today - timedelta(days=1)
            yesterday = yesterday.replace(hour=23, minute=59, second=59)

            earlier_day = today - timedelta(days=number_of_records)
            earlier_day = earlier_day.replace(hour=0, minute=0, second=1)

            d = {}
            for input_name, input_value in inputs.iteritems():
                if d == "input_date_time":
                    continue
                d[input_name] = input_value
            d["input_date_time__range"] = [earlier_day, yesterday]
            try:
                # entries = model.objects.filter(**d).order_by("-input_date_time")[:number_of_records]
                entries = model.objects.filter(**d).order_by("-input_date_time")
                i = entries.count()
                if entries.count() < (number_of_records - 1):
                    # let's fix it up
                    self.fixup(metric=model, from_date=earlier_day, to_date=yesterday)
                    entries = model.objects.filter(**d).order_by("-input_date_time")
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
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_app = models.TextField(verbose_name="alloc_speed_test", default="alloc_speed_test",  choices=[(0, "alloc_speed_test")])
    output_one_malloc_free_wu = models.IntegerField(verbose_name="Time in ns (WU)")
    output_one_malloc_free_threaded = models.IntegerField(verbose_name="Time in ns (Threaded)")
    tag = "analytics"

    def __str__(self):
        return "{}..{}..{}..{}".format(self.key, self.output_one_malloc_free_wu, self.output_one_malloc_free_threaded, self.input_date_time)


class WuLatencyAllocStack(models.Model):
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_app = models.TextField(verbose_name="wu_latency_test: alloc_stack", default="wu_latency_test", choices=[(0, "wu_latency_test")])
    output_min = models.IntegerField(verbose_name="Min (ns)")
    output_max = models.IntegerField(verbose_name="Max (ns)")
    output_avg = models.IntegerField(verbose_name="Avg (ns)")

    def __str__(self):
        return "{}..{}..{}..{}".format(self.key, self.output_min, self.output_avg, self.output_max)

class WuLatencyUngated(models.Model):
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    key = models.CharField(max_length=30, verbose_name="Git tag")
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.TextField(verbose_name="wu_latency_test: Ungated WU", default="wu_latency_test", choices=[(0, "wu_latency_test")])
    output_min = models.IntegerField(verbose_name="Min (ns)")
    output_max = models.IntegerField(verbose_name="Max (ns)")
    output_avg = models.IntegerField(verbose_name="Avg (ns)")

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
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_ndata_min = models.IntegerField(verbose_name="ndata min", default=8)
    input_ndata_max = models.IntegerField(verbose_name="ndata min", default=8)
    input_nparity_min = models.IntegerField(verbose_name="nparity min", default=4)
    input_stridelen_min = models.IntegerField(verbose_name="strideline min", default=4096)
    input_stridelen_max = models.IntegerField(verbose_name="strideline max", default=4096)

    output_encode_latency_min = models.IntegerField(verbose_name="Encode Latency min")
    output_encode_latency_max = models.IntegerField(verbose_name="Encode Latency max")
    output_encode_latency_avg = models.IntegerField(verbose_name="Encode Latency avg")

    output_encode_throughput_min = models.IntegerField(verbose_name="Encode Throughput min")
    output_encode_throughput_max = models.IntegerField(verbose_name="Encode Throughput max")
    output_encode_throughput_avg = models.IntegerField(verbose_name="Encode Throughput avg")

    output_recovery_latency_min = models.IntegerField(verbose_name="Recovery Latency min")
    output_recovery_latency_max = models.IntegerField(verbose_name="Recovery Latency max")
    output_recovery_latency_avg = models.IntegerField(verbose_name="Recovery Latency avg")

    output_recovery_throughput_min = models.IntegerField(verbose_name="Recovery Throughput min")
    output_recovery_throughput_max = models.IntegerField(verbose_name="Recovery Throughput max")
    output_recovery_throughput_avg = models.IntegerField(verbose_name="Recovery Throughput avg")

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
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_iterations = models.IntegerField(verbose_name="Iterations", default=10)
    input_coherent = models.TextField(verbose_name="Coherent/Non", default="Coherent", choices=[(0, "Coherent"), (1, "Non-coherent")])
    input_plain = models.TextField(verbose_name="Plain/DMA", default="Plain", choices=[(0, "Plain"), (1, "DMA")])
    input_size = models.IntegerField(verbose_name="Size in KB", choices=[(0, "4"), (1, "8"), (2, "16"), (3, "32"), (4, "64")])
    output_latency_units = models.TextField(verbose_name="Latency units")
    output_latency_min = models.IntegerField(verbose_name="Latency min")
    output_latency_max = models.IntegerField(verbose_name="Latency max")
    output_latency_avg = models.IntegerField(verbose_name="Latency max")
    input_latency_perf_name = models.TextField(verbose_name="Latency perf name")
    output_average_bandwith = models.IntegerField(verbose_name="Average Bandwidth in Gbps")
    input_average_bandwith_perf_name = models.TextField(verbose_name="Average Bandwidth perf name")

    def __str__(self):
        return str(self.__dict__)


class BcopyFloodDmaPerformance(models.Model):
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_n = models.IntegerField(verbose_name="N", default=0, choices=[(0, "1"), (1, "2"), (2, "4"), (3, "8"), (4, "16"), (5, "32"), (6, "64")])
    input_size = models.IntegerField(verbose_name="Size in KB", choices=[(0, "4"), (1, "8"), (2, "16"), (3, "32"), (4, "64")])
    output_latency_units = models.TextField(verbose_name="Latency units")
    output_latency_min = models.IntegerField(verbose_name="Latency min")
    output_latency_max = models.IntegerField(verbose_name="Latency max")
    output_latency_avg = models.IntegerField(verbose_name="Latency avg")
    input_latency_perf_name = models.TextField(verbose_name="Latency perf name")
    output_average_bandwith = models.IntegerField(verbose_name="Average Bandwidth in Gbps")
    input_average_bandwith_perf_name = models.TextField(verbose_name="Average Bandwidth perf name")

    def __str__(self):
        return str(self.__dict__)


class EcVolPerformance(models.Model):
    interpolated = models.BooleanField(default=False)
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_app = models.CharField(max_length=20, default="voltest", choices=[(0, "voltest")])
    output_ecvol_ec_stats_latency_ns_max = models.IntegerField(verbose_name="Latency max", default=-1)
    output_ecvol_ec_stats_latency_ns_avg = models.IntegerField(verbose_name="Latency avg", default=-1)
    output_ecvol_ec_stats_latency_ns_min = models.IntegerField(verbose_name="Latency min", default=-1)
    output_ecvol_ec_stats_iops = models.IntegerField(verbose_name="IOPS", default=-1)


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
    status = models.CharField(max_length=30, verbose_name="Status", default=RESULTS["PASSED"])
    interpolated = models.BooleanField(default=False)
    input_date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    input_frame_size = models.IntegerField(verbose_name="Fixed Frame Size Test", choices=[(0, 1500), (1, 1000), (2, 200), (3, 9000), (4, 16380), (5, 64)])
    output_throughput = models.FloatField(verbose_name="Throughput in Mbps")
    output_latency_avg = models.FloatField(verbose_name="Latency Avg in us")
    output_latency_max = models.FloatField(verbose_name="Latency Max in us")
    output_latency_min = models.FloatField(verbose_name="Latency Min in us")
    output_jitter_min = models.FloatField(verbose_name="Jitter min in us", default=0)
    output_jitter_max = models.FloatField(verbose_name="Jitter max in us", default=0)
    output_jitter_avg = models.FloatField(verbose_name="Jitter avg in us", default=0)

    output_pps = models.IntegerField(verbose_name="Packets per sec", default=0)
    input_mode = models.CharField(verbose_name="Port modes (25, 50 or 100 G)", max_length=10, choices=[(0, "25G"), (1, "50G"), (2, "100G")])
    input_version = models.CharField(verbose_name="Version", max_length=50)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class VoltestPerformance(models.Model):
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
    output_VOL_TYPE_BLK_EC_write_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_Bandwidth_avg", default=0)
    output_VOL_TYPE_BLK_EC_write_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_write_Bandwidth_total", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_max = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_max", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_avg", default=-1)
    output_VOL_TYPE_BLK_EC_read_latency_min = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_latency_min", default=-1)
    output_VOL_TYPE_BLK_EC_read_IOPS = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_IOPS", default=-1)
    output_VOL_TYPE_BLK_EC_read_Bandwidth_avg = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_Bandwidth avg", default=0)
    output_VOL_TYPE_BLK_EC_read_Bandwidth_total = models.IntegerField(verbose_name="output_VOL_TYPE_BLK_EC_read_Bandwidth total", default=-1)

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
    }
}

