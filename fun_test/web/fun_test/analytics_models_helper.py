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
from web.fun_test.metrics_models import MetricChart, MetricsRunTime
from web.fun_test.db_fixup import prepare_status
from fun_global import RESULTS, get_datetime_from_epoch_time, get_epoch_time_from_datetime
from dateutil.parser import parse
from fun_settings import MAIN_WEB_APP

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
from lib.system.fun_test import *
from web.fun_test.models_helper import add_jenkins_job_id_map, add_metrics_data_run_time
from django.utils import timezone
from dateutil import parser
from fun_global import PerfUnit, FunPlatform, get_current_epoch_time_in_ms, get_localized_time
import iso8601


def get_time_from_timestamp(timestamp):
    time_obj = parse(timestamp)
    return time_obj


def invalidate_goodness_cache():
    charts = MetricChart.objects.all()
    for chart in charts:
        chart.goodness_cache_valid = False
        chart.save()


def save_entry(entry, run_time=None):
    dry_run = fun_test.get_job_environment_variable("dry_run")
    if not dry_run:
        if run_time:
            # fun_test.log("Adding runtime properties")
            # fun_test.log("Run time props are {}".format(run_time))
            date_time = entry.input_date_time
            run_time_id = add_metrics_data_run_time(run_time=run_time, date_time=date_time)
            entry.run_time_id = run_time_id
        entry.save()
    else:
        try:
            fun_test.log("Dry run. Printing potential db entry")
            result = {}
            fields = entry._meta.get_fields()
            for field in fields:
                result[field.name] = getattr(entry, field.name)

            for key, value in result.iteritems():
                fun_test.log("DB entry: {}: {}".format(key, value))
        except Exception as ex:
            fun_test.critical(str(ex))
    return

def set_metrics_data_run_time():
    result = {}
    result["lsf_job_id"] = None
    result["suite_execution_id"] = fun_test.get_suite_execution_id()
    result["jenkins_build_number"] = None
    result["build_properties"] = fun_test.get_suite_run_time_environment_variable("bld_props")
    result["version"] = fun_test.get_version()
    result["associated_suites"] = None
    return result

def get_data_collection_time(tag=None):
    key = "data_collection_time"
    now_epoch = get_current_epoch_time_in_ms()
    now_time = get_datetime_from_epoch_time(now_epoch)
    result = now_time
    if fun_test.suite_execution_id:
        if tag:
            date_time_collection_objects = MetricsRunTime.objects.filter(name=key)
            match_found = False
            if date_time_collection_objects.exists():
                value = date_time_collection_objects[0].value
                epoch_value_in_tag = value.get(tag, None)
                if epoch_value_in_tag:
                    date_time_by_tag = get_datetime_from_epoch_time(epoch_value_in_tag)
                    if is_same_day(date_time_obj_a=now_time, date_time_obj_b=date_time_by_tag):
                        match_found = True
                        result = date_time_by_tag
                if not match_found:
                    MetricsRunTime.update_value_data(name=key, value_key=tag, value_data=now_epoch)
            else:
                MetricsRunTime(name=key, value={tag: now_epoch}).save()
        else:
            stored_data_collection_time_epoch = fun_test.get_stored_environment_variable(key)
            if not stored_data_collection_time_epoch:
                fun_test.update_job_environment_variable(key, get_current_epoch_time_in_ms())
                stored_data_collection_time_epoch = fun_test.get_stored_environment_variable(key)
            if type(stored_data_collection_time_epoch) in [str, unicode]:  # For legacy cases only
                result = iso8601.parse_date(stored_data_collection_time_epoch)
            else:
                result = get_datetime_from_epoch_time(stored_data_collection_time_epoch)

    return result


def is_same_day(date_time_obj_a, date_time_obj_b):
    return date_time_obj_a.day == date_time_obj_b.day and date_time_obj_a.month == date_time_obj_b.month and \
           date_time_obj_a.year == date_time_obj_b.year


def _update_run_time(tag, value=None, date_time_details=None):
    current_time = get_data_collection_time()
    if date_time_details and value:
        value[tag] = {}
        value[tag]["data_collection_time"] = str(current_time)
        date_time_details.value = value
        date_time_details.save()
    else:
        value = {tag: {"data_collection_time": str(current_time)}}
        MetricsRunTime(name="data_collection_time", value=value).save()
    return get_data_collection_time(tag=tag)


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

    def add_entry(self, run_time=None, **kwargs):
        inputs = {}
        if "key" in kwargs:
            inputs["key"] = kwargs["key"]
        outputs = {}
        # if run_time:
        #     kwargs["run_time"] = run_time
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
            # if run_time:
            #     if hasattr(o, "run_time"):
            #         setattr(o, "run_time", run_time)
            save_entry(o, run_time=run_time)
            return None
        except ObjectDoesNotExist:
            o = self.model(**kwargs)
            save_entry(o, run_time=run_time)
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
            save_entry(entry)
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
            save_entry(one_entry)


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
                  read_99_latency_unit="usecs", read_99_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  version=-1):
        try:
            run_time = set_metrics_data_run_time()
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
            entry.output_write_iops_unit = write_iops_unit
            entry.output_read_iops_unit = read_iops_unit
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
            save_entry(entry, run_time=run_time)
        except ObjectDoesNotExist:
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
            save_entry(one_entry, run_time=run_time)


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
                for key, value in self.units.iteritems():
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
                result = True
            except Exception as ex:
                fun_test.critical(str(ex))
        except Exception as ex:
            fun_test.critical(str(ex))
            raise ex
        return result

    def set_units(self, validate=True, **kwargs):
        result = None
        try:
            m_obj = self.metric_model
            if validate:
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
                run_time = set_metrics_data_run_time()
                save_entry(m_obj, run_time=run_time)
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


def prepare_status_db(metric_ids):
    cache_valid = MetricsGlobalSettings.get_cache_validity()
    # chart_names = ["F1", "S1", "All metrics"]
    for metric_id in metric_ids:
        total_chart = MetricChart.objects.get(metric_model_name="MetricContainer", metric_id=metric_id)
        prepare_status(chart=total_chart, purge_old_status=False, cache_valid=cache_valid)
    ml.backup_dags()
    ml.set_global_cache(cache_valid=True)


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

if __name__ == "__main__inspur":

    # Helper for Inspur 871 (single disk failure)
    value_dict = {
        "date_time": get_data_collection_time(),
        "num_hosts": 1,
        "num_f1s": 1,
        "base_file_copy_time": 1.32,
        "copy_time_during_plex_fail": 2.13,
        "file_copy_time_during_rebuild": 3.123,
        "plex_rebuild_time": 4.12,
    }
    unit_dict = {
        "base_file_copy_time_unit":PerfUnit.UNIT_SECS,
        "copy_time_during_plex_fail_unit":PerfUnit.UNIT_SECS,
        "file_copy_time_during_rebuild_unit":PerfUnit.UNIT_SECS,
        "plex_rebuild_time_unit":PerfUnit.UNIT_SECS
    }
    model_name = "InspurSingleDiskFailurePerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))
    print "used generic helper to add an entry"

    # Helper for Inspur 875 (Data reconstruction)

    value_dict = {
        "date_time": get_data_collection_time(),
        "num_hosts": 1,
        "block_size": "Mixed",
        "operation": "Combined",
        "write_iops": 100,
        "read_iops": 200,
        "write_throughput": 300,
        "read_throughput": 400,
        "write_avg_latency": 500,
        "write_90_latency": 600,
        "write_95_latency": 700,
        "write_99_99_latency": 800,
        "write_99_latency": 900,
        "read_avg_latency": 1000,
        "read_90_latency": 1100,
        "read_95_latency": 1200,
        "read_99_99_latency": 1300,
        "read_99_latency": 1400,
        "plex_rebuild_time": 1500
    }
    unit_dict = {
    "write_iops_unit": PerfUnit.UNIT_OPS,
    "read_iops_unit": PerfUnit.UNIT_OPS,
    "write_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
    "read_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
    "write_avg_latency_unit": PerfUnit.UNIT_USECS,
    "write_90_latency_unit": PerfUnit.UNIT_USECS,
    "write_95_latency_unit": PerfUnit.UNIT_USECS,
    "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
    "write_99_latency_unit": PerfUnit.UNIT_USECS,
    "read_avg_latency_unit": PerfUnit.UNIT_USECS,
    "read_90_latency_unit": PerfUnit.UNIT_USECS,
    "read_95_latency_unit": PerfUnit.UNIT_USECS,
    "read_99_99_latency_unit": PerfUnit.UNIT_USECS,
    "read_99_latency_unit": PerfUnit.UNIT_USECS,
    "plex_rebuild_time_unit": PerfUnit.UNIT_SECS
    }
    model_name = "InspurDataReconstructionPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))
    print "used generic helper to add an entry"

if __name__ == "__main__crypto":

    dt = datetime.datetime(year=2019, month=9, day=24, hour=2, minute=12, second=33)
    data = 4
    for app in ["crypto_dp_tunnel_throughput", "ipsec_tunnel_throughput"]:
        value_dict = {
            "date_time": dt,
            "platform": FunPlatform.S1,
            "app": app,
            "throughput": data
        }
        unit_dict = {
            "throughput_unit": PerfUnit.UNIT_GBITS_PER_SEC
        }
        model_name = "TeraMarkCryptoPerformance"
        status = fun_test.PASSED
        try:
            generic_helper = ModelHelper(model_name=model_name)
            generic_helper.set_units(validate=True, **unit_dict)
            generic_helper.add_entry(**value_dict)
            generic_helper.set_status(status)
        except Exception as ex:
            fun_test.critical(str(ex))
        print ("used generic helper to add an entry")

    for app in ["crypto_dp_tunnel_throughput", "ipsec_tunnel_throughput"]:
        value_dict = {
            "date_time": get_data_collection_time(),
            "platform": FunPlatform.S1,
            "app": app,
            "throughput": data
        }
        unit_dict = {
            "throughput_unit": PerfUnit.UNIT_GBITS_PER_SEC
        }
        model_name = "TeraMarkCryptoPerformance"
        status = fun_test.PASSED
        try:
            generic_helper = ModelHelper(model_name=model_name)
            generic_helper.set_units(validate=True, **unit_dict)
            generic_helper.add_entry(**value_dict)
            generic_helper.set_status(status)
        except Exception as ex:
            fun_test.critical(str(ex))
        print ("used generic helper to add an entry")

if __name__ == "__main2__":
    dt = datetime.datetime(year=2019, month=9, day=22, hour=2, minute=12, second=33)
    value_dict = {
        "date_time": dt,
        "app": "pke_x25519_2k_tls_soak",
        "platform": "S1",
        "metric_name": "ECDHE_RSA_X25519_RSA_2K",
        "ops_per_sec": 123
    }
    unit_dict = {
        "ops_per_sec_unit": "Kops"
    }
    model_name = "PkeX25519TlsSoakPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))
    print "used generic helper to add an entry"

if __name__ == "__main234__":
    fun_test.suite_execution_id = 320
    # print get_data_collection_time(tag="ec_inspur_fs_teramark_multi_f1")
    a = get_data_collection_time(tag="John1")
    print a

    print get_epoch_time_from_datetime(a)

if __name__ == "__main__":
    value_dict = {
        "date_time": get_data_collection_time(),
        "num_hosts": 1,
        "num_ssd": 12,
        "num_volume": 12,
        "block_size": "8K",
        "io_depth": 64,
        "operation": "randread",
        "compression": False,
        "encryption": False,
        "compression_effort": 1,
        "key_size": 128,
        "xtweak": 128,
        "io_size": "128GB",
        "platform": FunPlatform.F1,

        "write_iops": 100,
        "read_iops": 200,
        "write_throughput": 300,
        "read_throughput": 400,
        "write_avg_latency": 500,
        "write_90_latency": 600,
        "write_95_latency": 700,
        "write_99_latency": 900,
        "write_99_99_latency": 800,
        "read_avg_latency": 1000,
        "read_90_latency": 1100,
        "read_95_latency": 1200,
        "read_99_latency": 1400,
        "read_99_99_latency": 1300
    }
    unit_dict = {
        "write_iops_unit": PerfUnit.UNIT_OPS,
        "read_iops_unit": PerfUnit.UNIT_OPS,
        "write_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
        "read_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
        "write_avg_latency_unit": PerfUnit.UNIT_USECS,
        "write_90_latency_unit": PerfUnit.UNIT_USECS,
        "write_95_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_avg_latency_unit": PerfUnit.UNIT_USECS,
        "read_90_latency_unit": PerfUnit.UNIT_USECS,
        "read_95_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_99_latency_unit": PerfUnit.UNIT_USECS
    }
    model_name = "RawVolumeNvmeTcpMultiHostPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))
    print "used generic helper to add an entry"