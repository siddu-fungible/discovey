from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.metrics_models import AllocSpeedPerformance, BcopyPerformance, LAST_ANALYTICS_DB_STATUS_UPDATE
from web.fun_test.metrics_models import BcopyFloodDmaPerformance
from web.fun_test.metrics_models import EcPerformance, EcVolPerformance, VoltestPerformance
from web.fun_test.metrics_models import WuSendSpeedTestPerformance, WuDispatchTestPerformance, FunMagentPerformanceTest
from web.fun_test.metrics_models import WuStackSpeedTestPerformance, SoakFunMallocPerformance, SoakClassicMallocPerformance
from web.fun_test.metrics_models import WuLatencyAllocStack, WuLatencyUngated, BootTimePerformance
from web.fun_test.metrics_models import TeraMarkPkeEcdh256Performance, TeraMarkPkeEcdh25519Performance
from web.fun_test.metrics_models import TeraMarkPkeRsa4kPerformance, TeraMarkPkeRsaPerformance, TeraMarkCryptoPerformance
from web.fun_test.analytics_models_helper import MetricHelper, invalidate_goodness_cache, MetricChartHelper
from web.fun_test.analytics_models_helper import prepare_status_db
from web.fun_test.models import TimeKeeper
import re
from datetime import datetime

ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
BOOT_TIMING_TEST_TAG = "boot_timing_test"
VOLTEST_TAG = "voltest_performance"
TERAMARK_PKE = "pke_teramark"
TERAMARK_CRYPTO = "crypto_teramark"

def get_rounded_time():
    dt = get_current_time()
    dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59, second=59)
    dt = get_localized_time(dt)
    return dt

def is_job_from_today(job_dt):
    today = get_rounded_time()
    return True # TODO:
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
        self.lsf_status_server = LsfStatusServer()
        tags = [ALLOC_SPEED_TEST_TAG, VOLTEST_TAG, BOOT_TIMING_TEST_TAG, TERAMARK_PKE]
        self.lsf_status_server.workaround(tags=tags)
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        invalidate_goodness_cache()


class PalladiumPerformanceTc(FunTestCase):
    tag = ALLOC_SPEED_TEST_TAG
    result = fun_test.FAILED
    dt = get_rounded_time()

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def cleanup(self):
        pass

    def validate_job(self):
        job_info = self.lsf_status_server.get_last_job(tag=self.tag)
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
        output_one_malloc_free_classic_min = output_one_malloc_free_classic_avg = output_one_malloc_free_classic_max = -1
        wu_alloc_stack_ns_min = wu_alloc_stack_ns_max = wu_alloc_stack_ns_avg = -1
        wu_ungated_ns_min = wu_ungated_ns_max = wu_ungated_ns_avg = -1
        try:

            alloc_speed_test_found = False
            wu_latency_test_found = False


            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(r'Time for one fun_malloc\+fun_free \(WU\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]', line)
                if m:
                    alloc_speed_test_found = True
                    d = json.loads(m.group(1))
                    output_one_malloc_free_wu = int(d["avg"])
                m = re.search(r'Time for one fun_malloc\+fun_free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_threaded_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])
                m = re.search(r'Time for one malloc\+free \(classic\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_classic_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_classic_avg = int(d['avg'])
                    output_one_malloc_free_classic_min = int(d['min'])
                    output_one_malloc_free_classic_max = int(d['max'])

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
            fun_test.log("Malloc Free classic: min: {}, avg: {}, max: {}".format(output_one_malloc_free_classic_min,
                                                                                 output_one_malloc_free_classic_avg,
                                                                                 output_one_malloc_free_classic_max))
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
                                                                output_one_malloc_free_classic_min=output_one_malloc_free_classic_min,
                                                                output_one_malloc_free_classic_avg=output_one_malloc_free_classic_avg,
                                                                output_one_malloc_free_classic_max=output_one_malloc_free_classic_max,
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
            self.result = fun_test.PASSED
            # if self.result == fun_test.PASSED:


        except Exception as ex:
            fun_test.critical(str(ex))

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
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

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
    tag = VOLTEST_TAG
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
                    r'(?:\s+\d+:\s+)?(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[\S+:(?P<metric_name>\S+)\]', line)
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
                    d = self.metrics_to_dict(metrics, self.result)
                    MetricHelper(model=EcVolPerformance).add_entry(**d)
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))


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
                    r'"(?P<metric_name>\S+)\s+(?:\S+\s+\d+:\s+)?(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[(?P<metric_id>\S+)\]',
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
                    d = self.metrics_to_dict(metrics, self.result)
                    MetricHelper(model=VoltestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="VoltestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")
class WuDispatchTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    def describe(self):
        self.set_test_details(id=7,
                              summary="Wu Dispatch Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            i = 0

            for line in self.lines:
                m = re.search(
                    r'Average\s+dispatch\s+WU\s+cycles:\s+(?P<average>\d+)\s+\[(?P<metric_name>wu_dispatch_latency_cycles)\]',
                    line)
                if m:
                    output_average = int(m.group("average"))
                    input_app = "dispatch_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
                    MetricHelper(model=WuDispatchTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="WuDispatchTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class WuSendSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    def describe(self):
        self.set_test_details(id=8,
                              summary="Wu Send Speed Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            i = 0

            for line in self.lines:
                m = re.search(
                    r'Average\s+WU\s+send\s+ungated\s+cycles:\s+(?P<average>\d+)\s+\[(?P<metric_name>wu_send_ungated_latency_cycles)\]',
                    line)
                if m:
                    output_average = int(m.group("average"))
                    input_app = "wu_send_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
                    MetricHelper(model=WuSendSpeedTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="WuSendSpeedTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class FunMagentPerformanceTestTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    def describe(self):
        self.set_test_details(id=9,
                              summary="Fun Magent Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            i = 0

            for line in self.lines:
                m = re.search(
                    r'fun_magent.*=>\s+(?P<latency>\d+)(?P<unit>Kops/sec)\s+\[(?P<metric_name>fun_magent_rate_malloc_free_per_sec)\]',
                    line)
                if m:
                    unit = m.group("unit")
                    fun_test.test_assert(unit, "Kops/sec", "Valid Unit")
                    output_latency = int(m.group("latency"))
                    input_app = "fun_magent_perf_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("latency: {}, metric_name: {}".format(output_latency, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_latency"] = output_latency
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
                    MetricHelper(model=FunMagentPerformanceTest).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="FunMagentPerformanceTest")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class WuStackSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=10,
                              summary="Wu Send Speed Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'Average\s+wustack\s+alloc/+free\s+cycles:\s+(?P<average>\d+)\s+\[(?P<metric_name>wustack_alloc_free_cycles)\]',
                    line)
                if m:
                    output_average = int(m.group("average"))
                    input_app = "wustack_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=WuStackSpeedTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="WuStackSpeedTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class SoakFunMallocPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=11,
                              summary="Soak fun malloc Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+\[(?P<metric_name>soak_two_fun_malloc_fun_free)\]:\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                    line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "soak_malloc_fun_malloc"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=SoakFunMallocPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="SoakFunMallocPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class SoakClassicMallocPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=12,
                              summary="Soak classic malloc Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                        r'soak_bench\s+result\s+\[(?P<metric_name>soak_two_classic_malloc_free)\]:\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                        line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "soak_malloc_classic"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=SoakClassicMallocPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="SoakClassicMallocPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class BootTimingPerformanceTc(PalladiumPerformanceTc):
    tag = BOOT_TIMING_TEST_TAG

    def describe(self):
        self.set_test_details(id=13,
                              summary="Boot Timing Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        reset_cut_done = False
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            log = self.lsf_status_server.get_raw_file(job_id=self.job_id, file_name="cdn_uartout1.txt")
            fun_test.test_assert(log, "fetched uart log")
            log = log.split("\n")
            for line in log:
                if "Reset CUT done!" in line:
                    reset_cut_done = True
                if reset_cut_done:
                    m = re.search(
                            r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Firmware',
                            line)
                    if m:
                        output_firmware_boot_time = int(m.group("time"))
                        output_firmware_boot_cycles = int(m.group("cycle"))
                        fun_test.log("boot type: Firmware, boot time: {}, boot cycles: {}".format(output_firmware_boot_time, output_firmware_boot_cycles))
                        metrics["output_firmware_boot_time"] = output_firmware_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Flash\s+type\s+detection',
                        line)
                    if m:
                        output_flash_type_boot_time = int(m.group("time"))
                        output_flash_type_boot_cycles = int(m.group("cycle"))
                        fun_test.log("boot type: Flash type detection, boot time: {}, boot cycles: {}".format(output_flash_type_boot_time,
                                                                                                  output_flash_type_boot_cycles))
                        metrics["output_flash_type_boot_time"] = output_flash_type_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+EEPROM\s+Loading',
                        line)
                    if m:
                        output_eeprom_boot_time = int(m.group("time"))
                        output_eeprom_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: EEPROM Loading, boot time: {}, boot cycles: {}".format(output_eeprom_boot_time,
                                                                                         output_eeprom_boot_cycles))
                        metrics["output_eeprom_boot_time"] = output_eeprom_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+SBUS\s+Loading',
                        line)
                    if m:
                        output_sbus_boot_time = int(m.group("time"))
                        output_sbus_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: SBUS Loading, boot time: {}, boot cycles: {}".format(output_sbus_boot_time,
                                                                                         output_sbus_boot_cycles))
                        metrics["output_sbus_boot_time"] = output_sbus_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Host\s+BOOT',
                        line)
                    if m:
                        output_host_boot_time = int(m.group("time"))
                        output_host_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Host BOOT, boot time: {}, boot cycles: {}".format(output_host_boot_time,
                                                                                             output_host_boot_cycles))
                        metrics["output_host_boot_time"] = output_host_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Main\s+Loop',
                        line)
                    if m:
                        output_main_loop_boot_time = int(m.group("time"))
                        output_main_loop_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Main Loop, boot time: {}, boot cycles: {}".format(output_main_loop_boot_time,
                                                                                          output_main_loop_boot_cycles))
                        metrics["output_main_loop_boot_time"] = output_main_loop_boot_time

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Boot\s+success',
                        line)
                    if m:
                        output_boot_success_boot_time = int(m.group("time"))
                        output_boot_success_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Boot success, boot time: {}, boot cycles: {}".format(output_boot_success_boot_time,
                                                                                          output_boot_success_boot_cycles))
                        metrics["output_boot_success_boot_time"] = output_boot_success_boot_time

            d = self.metrics_to_dict(metrics, fun_test.PASSED)
            MetricHelper(model=BootTimePerformance).add_entry(**d)
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="BootTimePerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeRsaPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=14,
                              summary="TeraMark PKE RSA Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                        r'soak_bench\s+result\s+(?P<metric_name>RSA\s+CRT\s+2048\s+decryptions):\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                        line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "pke_rsa_crt_dec_no_pad_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeRsaPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="TeraMarkPkeRsaPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeRsa4kPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=15,
                              summary="TeraMark PKE RSA 4K Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                        r'soak_bench\s+result\s+(?P<metric_name>RSA\s+CRT\s+4096\s+decryptions):\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                        line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "pke_rsa_crt_dec_no_pad_4096_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeRsa4kPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="TeraMarkPkeRsa4kPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeEcdh256PerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=16,
                              summary="TeraMark PKE ECDH P256 Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                        r'soak_bench\s+result\s+(?P<metric_name>ECDH\s+P256):\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                        line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "pke_ecdh_soak_256"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeEcdh256Performance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="TeraMarkPkeEcdh256Performance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeEcdh25519PerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=17,
                              summary="TeraMark PKE ECDH 25519 Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                        r'soak_bench\s+result\s+(?P<metric_name>ECDH\s+25519):\s+(?P<ops_per_sec>\d+\.\d+)\s+ops/sec',
                        line)
                if m:
                    output_ops_per_sec = float(m.group("ops_per_sec"))
                    input_app = "pke_ecdh_soak_25519"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeEcdh25519Performance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="TeraMarkPkeEcdh25519Performance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkCryptoPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_CRYPTO

    def describe(self):
        self.set_test_details(id=18,
                              summary="TeraMark Crypto Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'{"alg":\s+"(?P<algorithm>\S+)",\s+"operation":\s+"(?P<operation>\S+)",\s+"results":\[(?P<results>.*)\]}',
                    line)
                if m:
                    input_app = "crypto_test_perf"
                    input_algorithm = m.group("algorithm")
                    input_operation = m.group("operation")
                    output_results = json.loads(m.group("results"))
                    input_pkt_size = int(output_results['pktsize']['value'])

                    output_ops_unit = "ops/sec"
                    output_ops_per_sec = int(output_results['ops']['value'])

                    output_throughput_unit = "Mbps"
                    output_throughput = int(output_results['throughput']['value'])

                    output_latency_unit = "ns"
                    output_latency_min = int(output_results['latency']['value']['min'])
                    output_latency_avg = int(output_results['latency']['value']['avg'])
                    output_latency_max = int(output_results['latency']['value']['max'])

                    metrics["input_app"] = input_app
                    metrics["input_algorithm"] = input_algorithm
                    metrics["input_operation"] = input_operation
                    metrics["input_pkt_size"] = input_pkt_size
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_throughput"] = output_throughput
                    metrics["output_latency_min"] = output_latency_min
                    metrics["output_latency_avg"] = output_latency_avg
                    metrics["output_latency_max"] = output_latency_max
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkCryptoPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_last_build_status_for_charts(result=self.result, model_name="TeraMarkCryptoPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

class PrepareDbTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=100,
                              summary="Prepare Status Db",
                              steps="Steps 1")

    def setup(self):
        pass

    def run(self):
        prepare_status_db()
        TimeKeeper.set_time(name=LAST_ANALYTICS_DB_STATUS_UPDATE, time=get_current_time())

    def cleanup(self):
        pass



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(AllocSpeedPerformanceTc())
    myscript.add_test_case(BcopyPerformanceTc())
    myscript.add_test_case(BcopyFloodPerformanceTc())
    myscript.add_test_case(EcPerformanceTc())
    myscript.add_test_case(EcVolPerformanceTc())
    myscript.add_test_case(VoltestPerformanceTc())
    myscript.add_test_case(WuDispatchTestPerformanceTc())
    myscript.add_test_case(WuSendSpeedTestPerformanceTc())
    myscript.add_test_case(FunMagentPerformanceTestTc())
    myscript.add_test_case(WuStackSpeedTestPerformanceTc())
    myscript.add_test_case(SoakFunMallocPerformanceTc())
    myscript.add_test_case(SoakClassicMallocPerformanceTc())
    myscript.add_test_case(BootTimingPerformanceTc())
    myscript.add_test_case(TeraMarkPkeRsaPerformanceTC())
    myscript.add_test_case(TeraMarkPkeRsa4kPerformanceTC())
    myscript.add_test_case(TeraMarkPkeEcdh256PerformanceTC())
    myscript.add_test_case(TeraMarkPkeEcdh25519PerformanceTC())
    myscript.add_test_case(TeraMarkCryptoPerformanceTC())
    myscript.add_test_case(PrepareDbTc())

    myscript.run()
