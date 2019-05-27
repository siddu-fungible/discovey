import os
import django
import json
import random
from web.web_global import PRIMARY_SETTINGS_FILE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import VolumePerformanceEmulation, BltVolumePerformance, \
    TeraMarkFunTcpThroughputPerformance
from web.fun_test.metrics_models import AllocSpeedPerformance, WuLatencyAllocStack
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart
from web.fun_test.db_fixup import prepare_status
from fun_global import RESULTS
from dateutil.parser import parse
from fun_settings import MAIN_WEB_APP
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
from lib.system.fun_test import *
from web.fun_test.models_helper import add_jenkins_job_id_map
from django.utils import timezone
from dateutil import parser

def get_time_from_timestamp(timestamp):
    time_obj = parse(timestamp)
    return time_obj

def invalidate_goodness_cache():
    charts = MetricChart.objects.all()
    for chart in charts:
        chart.goodness_cache_valid = False
        chart.save()

def get_data_collection_time():
    result = get_current_time()
    if fun_test.suite_execution_id:
        result = fun_test.get_stored_environment_variable("data_collection_time")
        if not result:
            date_time = get_current_time()
            fun_test.update_job_environment_variable("data_collection_time", str(date_time))
            result = date_time
        else:
            result = parser.parse(result)
    return result


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
            return None
        except ObjectDoesNotExist:
            o = self.model(**kwargs)
            o.save()
            return o.id

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
        return self.model.objects.order_by("-input_date_time")[0]


class MetricChartHelper(object):
    def __init__(self, chart_name, metric_model_name):
        self.chart_name = chart_name
        self.metric_model_name = metric_model_name
        self.chart = MetricChart.objects.get(chart_name=chart_name, metric_model_name=metric_model_name)

    def get_chart(self):
        return self.chart

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

    @staticmethod
    def get_charts_by_model_name(metric_model_name):
        charts = MetricChart.objects.filter(metric_model_name=metric_model_name)
        return charts


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

    def add_entry(self, key, volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw,
                  read_bw, write_latency, read_latency):
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


class VolumePerformanceEmulationHelper(MetricHelper):
    model = VolumePerformanceEmulation

    def __init__(self):
        super(VolumePerformanceEmulationHelper, self).__init__(model=self.model)

    def add_entry(self, date_time, volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw,
                  read_bw, write_latency, read_latency, write_90_latency=-1, write_95_latency=-1, write_99_latency=-1,
                  read_90_latency=-1, read_95_latency=-1, read_99_latency=-1, fio_job_name=""):
        try:
            entry = VolumePerformanceEmulation.objects.get(input_date_time=date_time,
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
            entry.output_write_90_latency = write_90_latency
            entry.output_write_95_latency = write_95_latency
            entry.output_write_99_latency = write_99_latency
            entry.output_read_90_latency = read_90_latency
            entry.output_read_95_latency = read_95_latency
            entry.output_read_99_latency = read_99_latency
            entry.input_fio_job_name = fio_job_name
            entry.save()
        except ObjectDoesNotExist:
            pass
            one_entry = VolumePerformanceEmulation(input_date_time=date_time,
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
                                                   output_read_latency=read_latency,
                                                   output_write_90_latency=write_90_latency,
                                                   output_write_95_latency=write_95_latency,
                                                   output_write_99_latency=write_99_latency,
                                                   output_read_90_latency=read_90_latency,
                                                   output_read_95_latency=read_95_latency,
                                                   output_read_99_latency=read_99_latency,
                                                   input_fio_job_name=fio_job_name)
            one_entry.save()


class BltVolumePerformanceHelper(MetricHelper):
    model = BltVolumePerformance

    def __init__(self):
        super(BltVolumePerformanceHelper, self).__init__(model=self.model)

    def add_entry(self, date_time, volume, test, block_size, io_depth, size, operation, num_ssd, num_volume,
                  fio_job_name, write_iops=-1, read_iops=-1,
                  write_throughput=-1, read_throughput=-1, write_avg_latency=-1, read_avg_latency=-1,
                  write_90_latency=-1,
                  write_95_latency=-1, write_99_latency=-1, read_90_latency=-1, read_95_latency=-1, read_99_latency=-1,
                  read_99_99_latency=-1, write_99_99_latency=-1,
                  write_iops_unit="ops", read_iops_unit="ops", write_throughput_unit="Mbps",
                  read_throughput_unit="Mbps", write_avg_latency_unit="usecs", read_avg_latency_unit="usecs",
                  write_90_latency_unit="usecs", write_95_latency_unit="usecs",
                  write_99_latency_unit="usecs", read_90_latency_unit="usecs", read_95_latency_unit="usecs",
                  read_99_latency_unit="usecs", read_99_99_latency_unit="usecs", write_99_99_latency_unit="usecs", version=-1):
        try:
            if version == -1:
                version = str(fun_test.get_version())
            entry = BltVolumePerformance.objects.get(input_date_time=date_time,
                                                     input_volume_type=volume,
                                                     input_test=test,
                                                     input_block_size=block_size,
                                                     input_io_depth=io_depth,
                                                     input_io_size=size,
                                                     input_operation=operation,
                                                     input_num_ssd=num_ssd,
                                                     input_num_volume=num_volume,
                                                     input_fio_job_name=fio_job_name,
                                                     input_version=version)
            entry.output_write_iops = write_iops
            entry.output_read_iops = read_iops
            entry.output_write_throughput = write_throughput
            entry.output_read_throughput = read_throughput
            entry.output_write_avg_latency = write_avg_latency
            entry.output_read_avg_latency = read_avg_latency
            entry.output_write_90_latency = write_90_latency
            entry.output_write_95_latency = write_95_latency
            entry.output_write_99_latency = write_99_latency
            entry.output_write_99_99_latency = write_99_99_latency
            entry.output_read_90_latency = read_90_latency
            entry.output_read_95_latency = read_95_latency
            entry.output_read_99_latency = read_99_latency
            entry.output_read_99_99_latency = read_99_99_latency
            entry.output_write_iops_unit = write_iops
            entry.output_read_iops_unit = read_iops
            entry.output_write_throughput_unit = write_throughput_unit
            entry.output_read_throughput_unit = read_throughput_unit
            entry.output_write_avg_latency_unit = write_avg_latency_unit
            entry.output_read_avg_latency_unit = read_avg_latency_unit
            entry.output_write_90_latency_unit = write_90_latency_unit
            entry.output_write_95_latency_unit = write_95_latency_unit
            entry.output_write_99_latency_unit = write_99_latency_unit
            entry.output_write_99_99_latency_unit = write_99_99_latency_unit
            entry.output_read_90_latency_unit = read_90_latency_unit
            entry.output_read_95_latency_unit = read_95_latency_unit
            entry.output_read_99_latency_unit = read_99_latency_unit
            entry.output_read_99_99_latency_unit = read_99_99_latency_unit
            entry.save()
        except ObjectDoesNotExist:
            fun_test.log("Adding new entry into model using helper")
            one_entry = BltVolumePerformance(input_date_time=date_time,
                                             input_volume_type=volume,
                                             input_test=test,
                                             input_block_size=block_size,
                                             input_io_depth=io_depth,
                                             input_io_size=size,
                                             input_operation=operation,
                                             input_num_ssd=num_ssd,
                                             input_num_volume=num_volume,
                                             input_fio_job_name=fio_job_name,
                                             input_version=version,
                                             output_write_iops=write_iops,
                                             output_read_iops=read_iops,
                                             output_write_throughput=write_throughput,
                                             output_read_throughput=read_throughput,
                                             output_write_avg_latency=write_avg_latency,
                                             output_read_avg_latency=read_avg_latency,
                                             output_write_90_latency=write_90_latency,
                                             output_write_95_latency=write_95_latency,
                                             output_write_99_latency=write_99_latency,
                                             output_write_99_99_latency=write_99_99_latency,
                                             output_read_90_latency=read_90_latency,
                                             output_read_95_latency=read_95_latency,
                                             output_read_99_latency=read_99_latency,
                                             output_read_99_99_latency=read_99_99_latency,
                                             output_write_iops_unit=write_iops_unit,
                                             output_read_iops_unit=read_iops_unit,
                                             output_write_throughput_unit=write_throughput_unit,
                                             output_read_throughput_unit=read_throughput_unit,
                                             output_write_avg_latency_unit=write_avg_latency_unit,
                                             output_read_avg_latency_unit=read_avg_latency_unit,
                                             output_write_90_latency_unit=write_90_latency_unit,
                                             output_write_95_latency_unit=write_95_latency_unit,
                                             output_write_99_latency_unit=write_99_latency_unit,
                                             output_write_99_99_latency_unit=write_99_99_latency_unit,
                                             output_read_90_latency_unit=read_90_latency_unit,
                                             output_read_95_latency_unit=read_95_latency_unit,
                                             output_read_99_latency_unit=read_99_latency_unit,
                                             output_read_99_99_latency_unit=read_99_99_latency_unit)
            one_entry.save()
            try:
                fun_test.log("Entering the jenkins job id map entry for {} and  {}".format(date_time, version))
                completion_date = timezone.localtime(one_entry.input_date_time)
                completion_date = str(completion_date).split(":")
                completion_date = completion_date[0] + ":" + completion_date[1]
                build_date = parser.parse(completion_date)
                suite_execution_id = fun_test.get_suite_execution_id()
                add_jenkins_job_id_map(jenkins_job_id=0,
                                       fun_sdk_branch="",
                                       git_commit="",
                                       software_date=0,
                                       hardware_version="",
                                       completion_date=completion_date,
                                       build_properties="", lsf_job_id="",
                                       sdk_version=version, build_date=build_date, suite_execution_id=suite_execution_id)
            except Exception as ex:
                fun_test.critical(str(ex))


class AllocSpeedPerformanceHelper(MetricHelper):
    model = AllocSpeedPerformance

    def __init__(self):
        super(AllocSpeedPerformanceHelper, self).__init__(model=self.model)

    def add_entry(self, key, input_date_time, input_app, output_one_malloc_free_wu, output_one_malloc_free_threaded,
                  output_one_malloc_free_classic_avg,
                  output_one_malloc_free_classic_min, output_one_malloc_free_classic_max):
        try:
            entry = AllocSpeedPerformance.objects.get(key=key, input_app=input_app, input_date_time=input_date_time)
            entry.output_one_malloc_free_wu = output_one_malloc_free_wu
            entry.output_one_malloc_free_threaded = output_one_malloc_free_threaded
            entry.output_one_malloc_free_classic_min = output_one_malloc_free_classic_min
            entry.output_one_malloc_free_classic_avg = output_one_malloc_free_classic_avg
            entry.output_one_malloc_free_classic_max = output_one_malloc_free_classic_max
            entry.save()
        except ObjectDoesNotExist:
            pass
            one_entry = AllocSpeedPerformance(key=key,
                                              input_app=input_app,
                                              input_date_time=input_date_time,
                                              output_one_malloc_free_wu=output_one_malloc_free_wu,
                                              output_one_malloc_free_threaded=output_one_malloc_free_threaded,
                                              output_one_malloc_free_classic_min=output_one_malloc_free_classic_min,
                                              output_one_malloc_free_classic_avg=output_one_malloc_free_classic_avg,
                                              output_one_malloc_free_classic_max=output_one_malloc_free_classic_max)
            one_entry.save()


class ModelHelper(MetricHelper):
    model = None
    units = None
    id = None

    def __init__(self, model_name):
        self.model = app_config.get_metric_models()[model_name]
        m_obj = self.model()
        self.metric_model = m_obj

    def add_entry(self, **kwargs):
        result = None
        try:
            self.id = None
            m_obj = self.metric_model
            units = {}
            for key, value in kwargs.iteritems():
                if key.endswith("_unit"):
                    units[key] = value
            if units != {}:
                self.units = units
            if not self.units:
                raise Exception('No units provided. Please provide the required units')
            else:
                for key,value in self.units.iteritems():
                    kwargs[key] = value
            new_kwargs = {}

            for key, value in kwargs.iteritems():
                if key == "timestamp":
                    key = "date_time"
                    value = get_time_from_timestamp(value)
                if hasattr(m_obj, "input_" + key):
                    new_kwargs["input_" + key] = value
                elif hasattr(m_obj, "output_" + key):
                    new_kwargs["output_" + key] = value
                    if not key.endswith("_unit"):
                        key_unit = key + "_unit"
                        if not key_unit in self.units:
                            raise Exception('No matching units for the output {} found'.format(key))
                elif hasattr(m_obj, key):
                    new_kwargs[key] = value
            try:
                self.id = super(ModelHelper, self).add_entry(**new_kwargs)
                if "input_version" in new_kwargs and "input_date_time" in new_kwargs:
                    date_time = timezone.localtime(new_kwargs["input_date_time"])
                    date_time = str(date_time).split(":")
                    completion_date = date_time[0] + ":" + date_time[1]
                    build_date = parser.parse(completion_date)
                    version = new_kwargs["input_version"]
                    suite_execution_id = fun_test.get_suite_execution_id()
                    add_jenkins_job_id_map(jenkins_job_id=0,
                                           fun_sdk_branch="",
                                           git_commit="",
                                           software_date=0,
                                           hardware_version="",
                                           completion_date=completion_date,
                                           build_properties="", lsf_job_id="",
                                           sdk_version=version, build_date=build_date, suite_execution_id=suite_execution_id)
                result = True
            except Exception as ex:
                fun_test.critical(str(ex))
        except Exception as ex:
            fun_test.critical(str(ex))
            raise ex
        return result

    def set_units(self, **kwargs):
        result = None
        try:
            m_obj = self.metric_model
            for key, value in kwargs.iteritems():
                if not hasattr(m_obj, "output_" + key):
                    raise Exception("Provided units do not match any output - {}".format(key))
            self.units = kwargs
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
            raise ex
        return result

    def set_status(self, status):
        result = None
        try:
            if self.id:
                m_obj = self.model.objects.get(id=self.id)
                if hasattr(m_obj, "status"):
                    setattr(m_obj, "status", status)
                if not self.units:
                    raise Exception('No units provided. Please provide the required units')
                m_obj.save()
                result = True
            else:
                raise Exception("Set status failed")
        except Exception as ex:
            fun_test.critical(str(ex))
            raise ex
        return result



class WuLatencyAllocStackHelper(MetricHelper):
    model = WuLatencyAllocStack

    def __init__(self):
        super(WuLatencyAllocStackHelper, self).__init__(model=self.model)

    def add_entry(self, key, input_date_time, input_app, output_min, output_avg, output_max):
        entry = WuLatencyAllocStack


def prepare_status_db(chart_names):
    global_setting = MetricsGlobalSettings.objects.first()
    cache_valid = global_setting.cache_valid
    # chart_names = ["F1", "S1", "All metrics"]
    for chart_name in chart_names:
        total_chart = MetricChart.objects.get(metric_model_name="MetricContainer", chart_name=chart_name)
        prepare_status(chart=total_chart, purge_old_status=False, cache_valid=cache_valid)
    global_setting.cache_valid = True
    global_setting.save()


if __name__ == "__main2__":
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
                p = PerformanceBlt(key=build, input1_block_size=block_size, input2_mode=mode, output1_iops=iops,
                                   output2_bw=bw, output3_latency=latency)
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
            p = PerformanceIkv(key=build, input1_put_value_size=put_value_size,
                               output1_put_per_seccond=output1_put_per_seccond)
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

if __name__ == "__main__":
    # prepare_status_db()
    # generic_helper = ModelHelper(model_name="TeraMarkJuniperNetworkingPerformance")
    # json_text = [{
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": False,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 64.0,
    #     "pps": 40697455.92,
    #     "throughput": 27999.85,
    #     "latency_min": 2.42,
    #     "latency_max": 14.83,
    #     "latency_avg": 5.03,
    #     "jitter_min": 0.0,
    #     "jitter_max": 4.24,
    #     "jitter_avg": 0.06,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # },
    # {
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": False,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 1500.0,
    #     "pps": 16430764.88,
    #     "throughput": 199798.1,
    #     "latency_min": 2.82,
    #     "latency_max": 8.76,
    #     "latency_avg": 4.12,
    #     "jitter_min": 0.0,
    #     "jitter_max": 0.73,
    #     "jitter_avg": 0.0,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # },
    # {
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": False,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 362.94,
    #     "pps": 40089054.46,
    #     "throughput": 120248.57,
    #     "latency_min": 2.45,
    #     "latency_max": 17.32,
    #     "latency_avg": 4.98,
    #     "jitter_min": 0.0,
    #     "jitter_max": 2.11,
    #     "jitter_avg": 0.05,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # },
    # {
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": True,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 64.0,
    #     "pps": 20348822.69,
    #     "throughput": 13999.99,
    #     "latency_min": 2.7,
    #     "latency_max": 6.77,
    #     "latency_avg": 4.11,
    #     "jitter_min": 0.0,
    #     "jitter_max": 3.05,
    #     "jitter_avg": 0.05,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # },
    # {
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": True,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 1500.0,
    #     "pps": 8215386.59,
    #     "throughput": 99899.1,
    #     "latency_min": 2.72,
    #     "latency_max": 5.8,
    #     "latency_avg": 3.69,
    #     "jitter_min": 0.0,
    #     "jitter_max": 0.57,
    #     "jitter_avg": 0.0,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # },
    # {
    #     "mode": "100G",
    #     "version": 6284,
    #     "timestamp": "2019-05-06 05:29:15.989421-07:00",
    #     "half_load_latency": True,
    #     "memory": "DDR",
    #     "flow_type": "NU_LE_VP_NU_FW",
    #     "frame_size": 362.94,
    #     "pps": 20044634.62,
    #     "throughput": 60124.61,
    #     "latency_min": 2.59,
    #     "latency_max": 10.39,
    #     "latency_avg": 3.66,
    #     "jitter_min": 0.0,
    #     "jitter_max": 2.04,
    #     "jitter_avg": 0.04,
    #     "num_flows": 128000000,
    #     "offloads": False,
    #     "protocol": "UDP"
    # }]
    #
    # unit = {}
    # unit["pps_unit"] = "pps"
    # unit["throughput_unit"] = "Mbps"
    # unit["latency_min_unit"] = "usecs"
    # unit["latency_max_unit"] = "usecs"
    # unit["latency_avg_unit"] = "usecs"
    # unit["jitter_min_unit"] = "usecs"
    # unit["jitter_max_unit"] = "usecs"
    # unit["jitter_avg_unit"] = "usecs"
    #
    # for line in json_text:
    #     status = fun_test.PASSED
    #     try:
    #         generic_helper.set_units(**unit)
    #         generic_helper.add_entry(**line)
    #         generic_helper.set_status(status)
    #     except Exception as ex:
    #         fun_test.critical(str(ex))
    #     print "used generic helper to add an entry"
    json_text = [{'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 53.345219, 'corpus_name': u'enwik8'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 56.596281870070456, 'corpus_name': u'misc'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 49.54274645518411, 'corpus_name': u'silesia'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 61.89778920481539, 'corpus_name': u'large'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 58.000550449492884, 'corpus_name': u'calgary'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 68.64279844752751, 'corpus_name': u'cantrbry'},
     {'effort_name': u'ZIP_EFFORT_AUTO', 'f1_compression_ratio': 74.07162314967105, 'corpus_name': u'artificl'}]

    unit_dict = {"f1_compression_ratio_unit": "number"}
    try:
        for d in json_text:
            generic_helper = ModelHelper(model_name="InspurZipCompressionRatiosPerformance")
            generic_helper.set_units(**unit_dict)
            d["date_time"] = get_data_collection_time()
            generic_helper.add_entry(**d)
            generic_helper.set_status(fun_test.PASSED)
            fun_test.log("Result posted to database: {}".format(d))
    except Exception as ex:
        fun_test.critical(ex.message)
