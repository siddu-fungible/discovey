from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.metrics_models import AllocSpeedPerformance, BcopyPerformance
from web.fun_test.metrics_models import BcopyFloodDmaPerformance
from web.fun_test.metrics_models import EcPerformance, EcVolPerformance, VoltestPerformance
from web.fun_test.metrics_models import WuLatencyAllocStack, WuLatencyUngated
from web.fun_test.analytics_models_helper import MetricHelper, invalidate_goodness_cache, MetricChartHelper
import re
from datetime import datetime

ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
VOLTEST_TAG = "voltest_performance"

def get_rounded_time():
    dt = get_current_time()
    dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59, second=59)
    dt = get_localized_time(dt)
    return dt

def is_job_from_today(job_dt):
    today = get_rounded_time()
    return (job_dt.year == today.year) and (job_dt.month == today.month) and (job_dt.day == today.day)

def set_last_build_status_for_charts(result, model_name):
    charts = MetricChartHelper.get_charts_by_model_name(metric_model_name=model_name)
    for chart in charts:
        chart.last_build_status = result
        chart.last_build_date = get_current_time()
        chart.save()


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        pass

    def cleanup(self):
        invalidate_goodness_cache()


class PalladiumPerformanceTc(FunTestCase):
    tag = ALLOC_SPEED_TEST_TAG
    result = fun_test.FAILED
    dt = get_rounded_time()

    def setup(self):
        pass

    def cleanup(self):
        pass

    def validate_job(self):
        lsf_status_server = LsfStatusServer()
        job_info = lsf_status_server.get_last_job(tag=self.tag)
        fun_test.test_assert(job_info, "Ensure one last job exists")
        lines = job_info["output_text"].split("\n")
        job_id = job_info["job_id"]
        dt = job_info["date_time"]

        fun_test.test_assert(is_job_from_today(dt), "Last job is from today")
        self.job_info = job_info
        self.lines = lines
        self.dt = dt
        self.job_id = job_id
        return True

    def metrics_to_dict(self, metrics, result):
        d = {}
        d["input_date_time"] = self.dt
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

class AllocSpeedPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Alloc speed test",
                              steps="Steps 1")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):

        output_one_malloc_free_wu = 0
        output_one_malloc_free_threaded = 0
        wu_alloc_stack_ns_min = wu_alloc_stack_ns_max = wu_alloc_stack_ns_avg = -1
        wu_ungated_ns_min = wu_ungated_ns_max = wu_ungated_ns_avg = -1
        try:

            alloc_speed_test_found = False
            wu_latency_test_found = False


            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(r'Time for one malloc/free \(WU\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]', line)
                if m:
                    alloc_speed_test_found = True
                    d = json.loads(m.group(1))
                    output_one_malloc_free_wu = int(d["avg"])
                m = re.search(r'Time for one malloc/free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])

                # wu_latency_test
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_alloc_stack_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_alloc_stack_ns_min = int(d["min"])
                    wu_alloc_stack_ns_avg = int(d["avg"])
                    wu_alloc_stack_ns_max = int(d["max"])
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_ungated_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_ungated_ns_min = int(d["min"])
                    wu_ungated_ns_avg = int(d["avg"])
                    wu_ungated_ns_max = int(d["max"])

            fun_test.log("Malloc Free threaded: {}".format(output_one_malloc_free_threaded))
            fun_test.log("Malloc Free WU: {}".format(output_one_malloc_free_wu))
            fun_test.log("wu_latency_test: wu_alloc_stack_ns: min: {}, avg: {}, max: {}".format(wu_alloc_stack_ns_min,
                                                                                                wu_alloc_stack_ns_avg,
                                                                                                wu_alloc_stack_ns_max))
            fun_test.log("wu_latency_test: wu_ungated_ns: min: {}, avg: {}, max: {}".format(wu_ungated_ns_min,
                                                                                            wu_ungated_ns_avg,
                                                                                            wu_ungated_ns_max))
            self.result = RESULTS["PASSED"]
        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=AllocSpeedPerformance).add_entry(status=self.result,
                                                                input_app="alloc_speed_test",
                                                                output_one_malloc_free_wu=output_one_malloc_free_wu,
                                                                output_one_malloc_free_threaded=output_one_malloc_free_threaded,
                                                                input_date_time=self.dt)

            MetricHelper(model=WuLatencyUngated).add_entry(status=self.result, input_app="wu_latency_test",
                                                           output_min=wu_ungated_ns_min,
                                                           output_max=wu_ungated_ns_max,
                                                           output_avg=wu_ungated_ns_avg,
                                                           input_date_time=self.dt)

            MetricHelper(model=WuLatencyAllocStack).add_entry(status=self.result,
                                                              input_app="wu_latency_test",
                                                              output_min=wu_alloc_stack_ns_min,
                                                              output_max=wu_alloc_stack_ns_max,
                                                              output_avg=wu_alloc_stack_ns_avg,
                                                              input_date_time=self.dt)

        set_last_build_status_for_charts(result=self.result, model_name="AllocSpeedPerformance")
        set_last_build_status_for_charts(result=self.result, model_name="WuLatencyUngated")
        set_last_build_status_for_charts(result=self.result, model_name="WuLatencyAllocStack")

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class BcopyPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Bcopy performance",
                              steps="Steps 1")

    def run(self):
        plain = ""
        coherent = ""
        size = -1
        iterations = -1
        latency_units = ""
        latency_min = -1
        latency_max = -1
        latency_avg = -1
        latency_perf_name = ""
        average_bandwidth = -1
        average_bandwidth_perf_name = ""
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>.*)\];\s+average bandwidth: (?P<average_bandwidth>\S+) \[(?P<average_bandwidth_perf_name>.*)\]',
                    line)

                if m:
                    stats_found = True
                    coherent = "Coherent"
                    if m.group("coherent") != "coherent":
                        coherent = "Non-coherent"
                    plain = "Plain"
                    if m.group("plain") != "plain":
                        plain = "DMA"
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))

                    iterations = int(m.group("iterations"))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_perf_name = m.group("latency_perf_name")
                    average_bandwidth = m.group("average_bandwidth")
                    try:
                        fun_test.test_assert(average_bandwidth.endswith("Gbps"), "Avg bw should be Gbps")
                        average_bandwidth = int(average_bandwidth.replace("Gbps", ""))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    average_bandwidth_perf_name = m.group("average_bandwidth_perf_name")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=BcopyPerformance).add_entry(status=self.result,
                                                           input_date_time=self.dt,
                                                           input_plain=plain,
                                                           input_coherent=coherent,
                                                           input_size=size,
                                                           input_iterations=iterations,
                                                           output_latency_units=latency_units,
                                                           output_latency_min=latency_min,
                                                           output_latency_max=latency_max,
                                                           output_latency_avg=latency_avg,
                                                           input_latency_perf_name=latency_perf_name,
                                                           output_average_bandwith=average_bandwidth,
                                                           input_average_bandwith_perf_name=average_bandwidth_perf_name)
        set_last_build_status_for_charts(result=self.result, model_name="BcopyPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class BcopyFloodPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=3,
                              summary="bcopy flood performance",
                              steps="Steps 1")

    def run(self):
        latency_units = latency_perf_name = average_bandwidth_perf_name = ""
        size = n = latency_min = latency_max = latency_avg = average_bandwidth = -1
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'bcopy flood with dma \((?P<N>\d+)\)\s+(?P<size>\S+);\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>\S+)\];\s+average bandwidth: (?P<average_bandwidth>\S+) \[(?P<average_bandwidth_perf_name>\S+)\]', line)
                if m:
                    n = m.group("N")
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_perf_name = m.group("latency_perf_name")
                    average_bandwidth = m.group("average_bandwidth")
                    try:
                        fun_test.test_assert(average_bandwidth.endswith("Gbps"), "Avg bw should be Gbps")
                        average_bandwidth = int(average_bandwidth.replace("Gbps", ""))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    average_bandwidth_perf_name = m.group("average_bandwidth_perf_name")

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=BcopyFloodDmaPerformance).add_entry(status=self.result,
                                                                   input_date_time=self.dt,
                                                                   input_n=n,
                                                                   input_size=size,
                                                                   output_latency_units=latency_units,
                                                                   output_latency_min=latency_min,
                                                                   output_latency_max=latency_max,
                                                                   output_latency_avg=latency_avg,
                                                                   input_latency_perf_name=latency_perf_name,
                                                                   output_average_bandwith=average_bandwidth,
                                                                   input_average_bandwith_perf_name=average_bandwidth_perf_name
                                                                   )
        set_last_build_status_for_charts(result=self.result, model_name="BcopyFloodDmaPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class EcPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=4,
                              summary="EC performance",
                              steps="Steps 1")

    def run(self):
        ec_encode_latency_min = ec_encode_latency_max = ec_encode_latency_avg = -1
        ec_encode_throughput_min = ec_encode_throughput_max = ec_encode_throughput_avg = -1
        ec_recovery_latency_min = ec_recovery_latency_max = ec_recovery_latency_avg = -1
        ec_recovery_throughput_min = ec_recovery_throughput_max = ec_recovery_throughput_avg = -1

        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_encode_latency\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_encode_latency_min = int(d["min"])
                    ec_encode_latency_max = int(d["max"])
                    ec_encode_latency_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="nsecs", message="perf_ec_encode_latency unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_encode_throughput\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_encode_throughput_min = int(d["min"])
                    ec_encode_throughput_max = int(d["max"])
                    ec_encode_throughput_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="Mbps",
                                                  message="perf_ec_encode_throughput unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_recovery_latency\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_recovery_latency_min = int(d["min"])
                    ec_recovery_latency_max = int(d["max"])
                    ec_recovery_latency_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="nsecs",
                                                  message="perf_ec_recovery_latency unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_recovery_throughput\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_recovery_throughput_min = int(d["min"])
                    ec_recovery_throughput_max = int(d["max"])
                    ec_recovery_throughput_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="Mbps",
                                                  message="perf_ec_encode_throughput unit")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=EcPerformance).add_entry(status=self.result,
                                                        input_date_time=self.dt,
                                                        output_encode_latency_min=ec_encode_latency_min,
                                                        output_encode_latency_max=ec_encode_latency_max,
                                                        output_encode_latency_avg=ec_encode_latency_avg,
                                                        output_encode_throughput_min=ec_encode_throughput_min,
                                                        output_encode_throughput_max=ec_encode_throughput_max,
                                                        output_encode_throughput_avg=ec_encode_throughput_avg,
                                                        output_recovery_latency_min=ec_recovery_latency_min,
                                                        output_recovery_latency_max=ec_recovery_latency_max,
                                                        output_recovery_latency_avg=ec_recovery_latency_avg,
                                                        output_recovery_throughput_min=ec_recovery_throughput_min,
                                                        output_recovery_throughput_max=ec_recovery_throughput_max,
                                                        output_recovery_throughput_avg=ec_recovery_throughput_avg
                                                        )
        set_last_build_status_for_charts(result=self.result, model_name="EcPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class EcVolPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=5,
                              summary="EC Vol performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'\S\s+(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[\S+:(?P<metric_name>\S+)\]', line)
                if m:
                    metric_type = m.group("metric_type")
                    value = m.group("value")
                    units = m.group("units")
                    metric_name = m.group("metric_name").lower()
                    if not ("ECVOL_EC_STATS_latency_ns".lower() in metric_name or "ECVOL_EC_STATS_iops".lower() in metric_name):
                        continue

                    try:  # Either a raw value or json value
                        j = json.loads(value)
                        for key, value in j.iteritems():
                            metrics["output_" + metric_name + "_" + key] = value
                    except:
                        metrics["output_" + metric_name] = value
                    try:
                        # if units not in ["mbps", "nsecs", "iops"]:
                        fun_test.simple_assert(units in ["mbps", "nsecs", "iops"], "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        pass
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        d = self.metrics_to_dict(metrics, self.result)
        if self.result == fun_test.PASSED:
            MetricHelper(model=EcVolPerformance).add_entry(**d)
        set_last_build_status_for_charts(result=self.result, model_name="EcVolPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class VoltestPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_TAG
    def describe(self):
        self.set_test_details(id=6,
                              summary="Voltest performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'"(?P<metric_name>\S+)\s+(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[(?P<metric_id>\S+)\]',
                    line)
                if m:
                    stats_found = True
                    metric_name = m.group("metric_name")
                    metric_type = m.group("metric_type")
                    value = m.group("value")
                    units = m.group("units")
                    metric_id = m.group("metric_id").lower()
                    allowed_metric_names = ["VOL_TYPE_BLK_LSV_write",
                                            "VOL_TYPE_BLK_LSV_read",
                                            "FILTER_TYPE_XTS_ENCRYPT",
                                            "FILTER_TYPE_XTS_DECRYPT",
                                            "FILTER_TYPE_DEFLATE",
                                            "FILTER_TYPE_INFLATE",
                                            "VOL_TYPE_BLK_EC_write",
                                            "VOL_TYPE_BLK_EC_read"]
                    if metric_name not in allowed_metric_names:
                        continue

                    if "andwidth" in metric_type.lower():
                        if "avg_op_bw_mbps" in line:
                            metric_type += "_avg"
                        elif "total_op_bw_mbps":
                            metric_type += "_total"

                    try:  # Either a raw value or json value
                        j = json.loads(value)
                        for key, value in j.iteritems():
                            metrics["output_" + metric_name + "_" + metric_type + "_" + key] = value
                    except Exception as ex:
                        metrics["output_" + metric_name + "_" + metric_type] = value

                    try:
                        fun_test.simple_assert(units in ["mbps", "nsecs", "iops"],
                                               "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        fun_test.critical(str(ex))

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        d = self.metrics_to_dict(metrics, self.result)
        if self.result == fun_test.PASSED:
            MetricHelper(model=VoltestPerformance).add_entry(**d)
        set_last_build_status_for_charts(result=self.result, model_name="VoltestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(AllocSpeedPerformanceTc())
    myscript.add_test_case(BcopyPerformanceTc())
    myscript.add_test_case(BcopyFloodPerformanceTc())
    myscript.add_test_case(EcPerformanceTc())
    myscript.add_test_case(EcVolPerformanceTc())
    myscript.add_test_case(VoltestPerformanceTc())

    myscript.run()
